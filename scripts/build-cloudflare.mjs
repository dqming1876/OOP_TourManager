import fs from 'node:fs';

const auth = fs.readFileSync('worker/auth.js', 'utf8').replaceAll('export async function', 'async function');
const accounts = fs.readFileSync('worker/accounts.js', 'utf8');
const reports = fs.readFileSync('worker/reports.js', 'utf8');
const operations = ['repository', 'service', 'route']
  .map(part => fs.readFileSync('worker/operations-' + part + '.js', 'utf8')).join('\n');
fs.mkdirSync('.cloudflare', { recursive: true });
fs.writeFileSync('.cloudflare/worker.js', [auth, accounts, operations, reports].join('\n') + `
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path.startsWith('/api/auth/') || path === '/api/profile') return accountsRoute(request, env);
    if (path.startsWith('/api/ops/')) return operationsRoute(request, env, path);
    if (path.startsWith('/api/')) return authRoute(request, env);
    if (path === '/admin.js' && !await authenticated(request, env)) {
      return new Response('Unauthorized', { status: 401, headers: { 'Cache-Control': 'no-store' } });
    }
    if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405 });
    const asset = await env.ASSETS.fetch(request);
    const response = new Response(asset.body, asset);
    response.headers.set('X-Content-Type-Options', 'nosniff');
    return response;
  }
};
`);
