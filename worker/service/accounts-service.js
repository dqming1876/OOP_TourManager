import { AccountsRepository } from '../database/accounts-repository.js';
import { AccessError, AppError, ConflictError, ValidationError } from '../domain/errors.js';
import { validCalendarDay } from '../domain/validation.js';
import { equal, passwordHash } from './passwords.js';
import { adminCookie, authenticated, customerCookie, sessionIdentity } from './session.js';

const loginAttempts = new Map();

function adminAccount(env) {
  return { id: 'admin', name: 'Quản trị viên', username: env.ADMIN_USERNAME, role: 'admin' };
}

function publicAccount({ id, name, username, email, phone, address, birthday }) {
  return { id, name, username, role: 'customer', email, phone, address, birthday };
}

function accounts(env) {
  if (!env.DB) throw new AppError(503, 'Hệ thống tài khoản chưa sẵn sàng.');
  return new AccountsRepository(env.DB);
}

export async function currentAccount(request, env) {
  if (await authenticated(request, env)) return adminAccount(env);
  const id = await sessionIdentity(request, env.ADMIN_SESSION_SECRET, customerCookie);
  const row = id && env.DB ? await accounts(env).findPublicById(id) : null;
  return row ? publicAccount(row) : null;
}

function credentials(body) {
  const username = typeof body.username === 'string' ? body.username.trim().toLowerCase() : '';
  if (!username || typeof body.password !== 'string' || body.password.length > 128) {
    throw new ValidationError('Vui lòng nhập tài khoản và mật khẩu.');
  }
  return { username, password: body.password };
}

function recordAttempt(request) {
  const key = request.headers.get('CF-Connecting-IP') || 'unknown';
  const now = Date.now();
  for (const [ip, attempt] of loginAttempts) {
    if (attempt.until <= now) loginAttempts.delete(ip);
    else break;
  }
  let attempt = loginAttempts.get(key);
  if (!attempt) {
    attempt = { count: 0, until: now + 300000 };
    loginAttempts.set(key, attempt);
  }
  if (attempt.count >= 12) throw new AppError(429, 'Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 5 phút.');
  attempt.count++;
  return key;
}

export async function loginAccount(request, env, body, adminOnly = false) {
  const { username, password } = credentials(body);
  const key = recordAttempt(request);
  if (username === env.ADMIN_USERNAME?.toLowerCase()) {
    if (!env.ADMIN_PASSWORD_SALT || !env.ADMIN_PASSWORD_HASH || !env.ADMIN_SESSION_SECRET) {
      throw new AppError(503, 'Tài khoản quản trị chưa được cấu hình.');
    }
    const hash = await passwordHash(password, env.ADMIN_PASSWORD_SALT);
    if (equal(hash, env.ADMIN_PASSWORD_HASH)) {
      loginAttempts.delete(key);
      return { user: adminAccount(env), cookie: adminCookie };
    }
  } else if (!adminOnly) {
    const row = await accounts(env).findByUsername(username);
    const hash = await passwordHash(password, row?.salt || 'dummy-login-salt');
    if (row && equal(hash, row.password_hash)) {
      loginAttempts.delete(key);
      return { user: publicAccount(row), cookie: customerCookie };
    }
  }
  throw new AccessError(401, 'Tài khoản hoặc mật khẩu không đúng.');
}

export async function registerAccount(request, env, body) {
  const { username, password } = credentials(body);
  const name = typeof body.name === 'string' ? body.name.trim() : '';
  if (!name || name.length > 80 || !/^[a-z0-9_]{3,32}$/.test(username) || password.length < 6) {
    throw new ValidationError('Nhập họ tên, tên đăng nhập 3–32 ký tự hợp lệ và mật khẩu tối thiểu 6 ký tự.');
  }
  const key = recordAttempt(request);
  const repository = accounts(env);
  if (username === env.ADMIN_USERNAME?.toLowerCase() || await repository.findByUsername(username)) {
    throw new ConflictError('Tên đăng nhập đã được sử dụng.');
  }
  const salt = crypto.randomUUID();
  const hash = await passwordHash(password, salt);
  if (!await repository.create({ id: crypto.randomUUID(), username, name, hash, salt })) {
    throw new ConflictError('Tên đăng nhập đã được sử dụng.');
  }
  loginAttempts.delete(key);
}

const profileFields = {
  name: ['Họ tên', 80], email: ['Email', 120], phone: ['Số điện thoại', 20],
  address: ['Địa chỉ', 250], birthday: ['Ngày sinh', 10],
};

function validatedProfile(body) {
  const invalid = field => new ValidationError(profileFields[field][0] + ' không hợp lệ.', field);
  const profile = {};
  for (const [field, [, limit]] of Object.entries(profileFields)) {
    const value = body[field] ?? '';
    if (typeof value !== 'string' || value.trim().length > limit) throw invalid(field);
    profile[field] = value.trim();
  }
  const { name, email, phone, birthday } = profile;
  if (!name) throw invalid('name');
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw invalid('email');
  if (phone && (!/^[0-9+ ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 8)) throw invalid('phone');
  if (birthday && !validCalendarDay(birthday)) throw invalid('birthday');
  return profile;
}

export async function saveCustomerProfile(request, env, body) {
  const user = await currentAccount(request, env);
  if (user?.role !== 'customer') throw new AccessError(401, 'Vui lòng đăng nhập tài khoản khách hàng.');
  const profile = validatedProfile(body);
  await accounts(env).updateProfile(user.id, profile);
  return { ...user, ...profile };
}
