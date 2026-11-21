import { AppError } from '../domain/errors.js';
import { currentAccount, loginAccount, registerAccount, saveCustomerProfile } from '../service/accounts-service.js';
import { adminCookie, authenticated, clearCookie, createSession, customerCookie } from '../service/session.js';
import { json, readObject, requirePost, withCookies } from './http.js';

export async function accountsRoute(request, env, path) {
  if (request.method === 'GET') {
    if (path === '/api/auth/me') {
      const user = await currentAccount(request, env);
      return json({ user: user?.toPublic() ?? null });
    }
    if (path === '/api/admin/session') return json({ authenticated: await authenticated(request, env) });
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
  if (path === '/api/profile') return json({ user: await saveCustomerProfile(request, env, body) });
  if (path === '/api/auth/register') {
    await registerAccount(request, env, body);
    return json({ ok: true }, 201);
  }
  const legacyAdmin = path === '/api/admin/login';
  const { user, cookie } = await loginAccount(request, env, body, legacyAdmin);
  const token = await createSession(cookie, env.ADMIN_SESSION_SECRET, user.role === 'customer' ? user.id : null);
  return withCookies(legacyAdmin ? { ok: true } : { user }, [
    clearCookie(cookie === adminCookie ? customerCookie : adminCookie), token,
  ]);
}
