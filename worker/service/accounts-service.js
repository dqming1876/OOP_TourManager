import { AccessError, AppError, ConflictError, ValidationError } from '../domain/errors.js';
import { AccountRole, AdministratorAccount, CustomerAccount } from '../domain/account.js';
import { equal, passwordHash } from './passwords.js';
import { adminCookie, authenticated, customerCookie, sessionIdentity } from './session.js';

function credentials(body) {
  const username = typeof body.username === 'string' ? body.username.trim().toLowerCase() : '';
  if (!username || typeof body.password !== 'string' || body.password.length > 128) {
    throw new ValidationError('Vui lòng nhập tài khoản và mật khẩu.');
  }
  return { username, password: body.password };
}

export class AccountsService {
  /** @param {import('../ports.js').AccountsPort|null} repository */
  constructor(repository, settings, attempts) {
    this.repository = repository;
    this.settings = settings;
    this.attempts = attempts;
  }

  #accounts() {
    if (!this.repository) throw new AppError(503, 'Hệ thống tài khoản chưa sẵn sàng.');
    return this.repository;
  }

  async currentAccount(request) {
    if (await authenticated(request, this.settings)) return new AdministratorAccount(this.settings.ADMIN_USERNAME);
    const id = await sessionIdentity(request, this.settings.ADMIN_SESSION_SECRET, customerCookie);
    const row = id && this.repository ? await this.#accounts().findPublicById(id) : null;
    return row ? new CustomerAccount(row) : null;
  }

  #recordAttempt(request) {
    const key = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Date.now();
    for (const [ip, attempt] of this.attempts) {
      if (attempt.until <= now) this.attempts.delete(ip);
      else break;
    }
    let attempt = this.attempts.get(key);
    if (!attempt) {
      attempt = { count: 0, until: now + 300000 };
      this.attempts.set(key, attempt);
    }
    if (attempt.count >= 12) throw new AppError(429, 'Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 5 phút.');
    attempt.count++;
    return key;
  }

  async loginAccount(request, body, adminOnly = false) {
    const { username, password } = credentials(body);
    const key = this.#recordAttempt(request);
    if (username === this.settings.ADMIN_USERNAME?.toLowerCase()) {
      if (!this.settings.ADMIN_PASSWORD_SALT || !this.settings.ADMIN_PASSWORD_HASH || !this.settings.ADMIN_SESSION_SECRET) {
        throw new AppError(503, 'Tài khoản quản trị chưa được cấu hình.');
      }
      const hash = await passwordHash(password, this.settings.ADMIN_PASSWORD_SALT);
      if (equal(hash, this.settings.ADMIN_PASSWORD_HASH)) {
        this.attempts.delete(key);
        return { user: new AdministratorAccount(this.settings.ADMIN_USERNAME).toPublic(), cookie: adminCookie };
      }
    } else if (!adminOnly) {
      const row = await this.#accounts().findByUsername(username);
      const hash = await passwordHash(password, row?.salt || 'dummy-login-salt');
      if (row && equal(hash, row.password_hash)) {
        this.attempts.delete(key);
        return { user: new CustomerAccount(row).toPublic(), cookie: customerCookie };
      }
    }
    throw new AccessError(401, 'Tài khoản hoặc mật khẩu không đúng.');
  }

  async registerAccount(request, body) {
    const { username, password } = credentials(body);
    const name = typeof body.name === 'string' ? body.name.trim() : '';
    if (!name || name.length > 80 || !/^[a-z0-9_]{3,32}$/.test(username) || password.length < 6) {
      throw new ValidationError('Nhập họ tên, tên đăng nhập 3–32 ký tự hợp lệ và mật khẩu tối thiểu 6 ký tự.');
    }
    const key = this.#recordAttempt(request);
    const repository = this.#accounts();
    if (username === this.settings.ADMIN_USERNAME?.toLowerCase() || await repository.findByUsername(username)) {
      throw new ConflictError('Tên đăng nhập đã được sử dụng.');
    }
    const salt = crypto.randomUUID();
    const hash = await passwordHash(password, salt);
    if (!await repository.create({ id: crypto.randomUUID(), username, name, hash, salt })) {
      throw new ConflictError('Tên đăng nhập đã được sử dụng.');
    }
    this.attempts.delete(key);
  }

  async saveCustomerProfile(request, body) {
    const user = await this.currentAccount(request);
    if (user?.role !== AccountRole.CUSTOMER) throw new AccessError(401, 'Vui lòng đăng nhập tài khoản khách hàng.');
    const profile = user.validateUpdate(body);
    await this.#accounts().updateProfile(user.id, profile);
    return { ...user.toPublic(), ...profile };
  }
}
