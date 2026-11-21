import { AppError } from '../domain/errors.js';
import { equal, hmac } from './passwords.js';

const sessionSeconds = 8 * 60 * 60;
const cookieOptions = '; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=';
export const adminCookie = 'dv_admin';
export const customerCookie = 'dv_user';

export function clearCookie(name) {
  return name + '=' + cookieOptions + '0';
}

export async function createSession(name, secret, customerId) {
  if (!secret) throw new AppError(503, 'Hệ thống tài khoản chưa sẵn sàng.');
  const expiry = Date.now() + sessionSeconds * 1000;
  const value = customerId ? customerId + '.' + expiry : String(expiry);
  return name + '=' + value + '.' + await hmac(value, secret) + cookieOptions + sessionSeconds;
}

export async function sessionIdentity(request, secret, name) {
  if (!secret) return null;
  const token = (request.headers.get('Cookie') || '').match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'))?.[1];
  if (!token) return null;
  const parts = token.split('.');
  const admin = name === adminCookie;
  if (parts.length !== (admin ? 2 : 3)) return null;
  const expiry = parts.at(-2);
  if (!/^\d+$/.test(expiry) || Number(expiry) < Date.now() || Number(expiry) > Date.now() + 9 * 3600000) return null;
  return equal(parts.at(-1), await hmac(parts.slice(0, -1).join('.'), secret)) ? (admin ? 'admin' : parts[0]) : null;
}

export async function authenticated(request, env) {
  return Boolean(await sessionIdentity(request, env.ADMIN_SESSION_SECRET, adminCookie));
}
