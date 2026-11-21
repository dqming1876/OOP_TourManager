import './build-cloudflare.mjs';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { Readable } from 'node:stream';
import { extname, resolve, sep } from 'node:path';
import { randomBytes } from 'node:crypto';
import { demoSql } from './demo-data.mjs';

const { makeWorker } = await import('./sqlite-worker.mjs');
const root = resolve('dist');
const adminPassword = process.env.MINGO_DEMO_PASSWORD || randomBytes(9).toString('base64url');
const mimeTypes = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png',
  '.jpeg': 'image/jpeg', '.jpg': 'image/jpeg', '.avif': 'image/avif',
};
const demo = makeWorker({
  adminPassword,
  seed: demoSql(),
  assets: { async fetch(request) {
    const path = new URL(request.url).pathname;
    const filename = resolve(root, '.' + decodeURIComponent(path === '/' ? '/index.html' : path));
    if (!filename.startsWith(root + sep) || filename.startsWith(resolve(root, 'server') + sep)) {
      return new Response('Not found', { status: 404 });
    }
    try {
      const body = request.method === 'HEAD' ? null : await readFile(filename);
      return new Response(body, { headers: { 'Content-Type': mimeTypes[extname(filename)] || 'application/octet-stream' } });
    } catch {
      return new Response('Not found', { status: 404 });
    }
  } },
});

const port = Number(process.env.MINGO_DEMO_PORT || 4173);
const server = createServer(async (incoming, outgoing) => {
  try {
    const host = incoming.headers.host;
    if (!['localhost:' + port, '127.0.0.1:' + port].includes(host)) {
      outgoing.writeHead(400).end('Use localhost');
      return;
    }
    const method = incoming.method;
    const body = method === 'GET' || method === 'HEAD' ? {} : { body: Readable.toWeb(incoming), duplex: 'half' };
    const response = await demo.fetch(new Request(new URL(incoming.url, 'http://' + host), {
      method, headers: incoming.headers, ...body,
    }));
    const headers = Object.fromEntries(response.headers);
    if (response.headers.has('Set-Cookie')) headers['set-cookie'] = response.headers.getSetCookie();
    outgoing.writeHead(response.status, headers);
    if (response.body) Readable.fromWeb(response.body).pipe(outgoing);
    else outgoing.end();
  } catch (error) {
    console.error(error.message);
    if (!outgoing.headersSent) outgoing.writeHead(500);
    outgoing.end();
  }
});
server.listen(port, '127.0.0.1', () => {
  console.log('Mingo demo: http://127.0.0.1:' + port);
  console.log('Admin demo_admin — mật khẩu phiên này:', adminPassword);
  console.log('Khách mingo_khach1 — mật khẩu mẫu: MingoDemo26!');
});
