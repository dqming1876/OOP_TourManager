import { AppError } from '../domain/errors.js';
import { adminCookie, authenticated, clearCookie, createSession, customerCookie } from '../service/session.js';
import { json, readObject, requirePost, withCookies } from './http.js';

export async function accountsRoute(request, path, accounts, settings) {
  if (request.method === 'GET') {
    if (path === '/api/auth/me') {
      const user = await accounts.currentAccount(request);
      return json({ user: user?.toPublic() ?? null });
    }
    if (path === '/api/admin/session') return json({ authenticated: await authenticated(request, settings) });
  }
  const login = path === '/api/auth/login' || path === '/api/admin/login';
  const logout = path === '/api/auth/logout' || path === '/api/admin/logout';
  if (!login && !logout && path !== '/api/profile' && path !== '/api/auth/register') {
    throw new AppError(404, 'Không tìm thấy chức năng.');
  }
  requirePost(request);
  if (logout) {
    const cookies = [clearCookie(adminCookie)];
    if (path === '/api/auth/logout') cookies.push(clearCookie(customerCookie));
    return withCookies({ ok: true }, cookies);
  }
  const body = await readObject(request, 8192);
  if (path === '/api/profile') return json({ user: await accounts.saveCustomerProfile(request, body) });
  if (path === '/api/auth/register') {
    await accounts.registerAccount(request, body);
    return json({ ok: true }, 201);
  }
  const legacyAdmin = path === '/api/admin/login';
  const { user, cookie } = await accounts.loginAccount(request, body, legacyAdmin);
  const token = await createSession(cookie, settings.ADMIN_SESSION_SECRET, user.role === 'customer' ? user.id : null);
  return withCookies(legacyAdmin ? { ok: true } : { user }, [
    clearCookie(cookie === adminCookie ? customerCookie : adminCookie), token,
  ]);
}
