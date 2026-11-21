import { accountsRoute } from './api/accounts-route.js';
import { errorResponse } from './api/http.js';
import { operationsRoute } from './api/operations-route.js';
import { authenticated } from './service/session.js';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname.startsWith('/api/ops/')) return await operationsRoute(request, env, url);
      if (url.pathname.startsWith('/api/')) return await accountsRoute(request, env, url.pathname);
      if (url.pathname === '/admin.js' && !await authenticated(request, env)) {
        return new Response('Unauthorized', { status: 401, headers: { 'Cache-Control': 'no-store' } });
      }
      if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405 });
      const asset = await env.ASSETS.fetch(request);
      const response = new Response(asset.body, asset);
      response.headers.set('X-Content-Type-Options', 'nosniff');
      return response;
    } catch (error) {
      return errorResponse(error);
    }
  },
};
