import { AccessError, AppError, ValidationError } from '../domain/errors.js';

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

export function withCookies(data, cookies, status = 200) {
  const response = json(data, status);
  for (const cookie of cookies) response.headers.append('Set-Cookie', cookie);
  return response;
}

export function requirePost(request) {
  if (request.method !== 'POST') throw new AppError(405, 'Phương thức không hợp lệ.');
  if (request.headers.get('Origin') !== new URL(request.url).origin) {
    throw new AccessError(403, 'Nguồn yêu cầu không hợp lệ.');
  }
}

export async function readObject(request, maxLength) {
  const raw = await request.text();
  if (raw.length > maxLength) throw new AppError(413, 'Dữ liệu quá lớn.');
  try {
    const body = JSON.parse(raw);
    if (body && !Array.isArray(body) && typeof body === 'object') return body;
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error;
  }
  throw new ValidationError('Dữ liệu không hợp lệ.');
}

export function errorResponse(error) {
  if (error instanceof AppError) return json({ error: error.message, field: error.field }, error.status);
  const requestId = crypto.randomUUID();
  console.error('Unexpected Worker error', { requestId, type: error?.name || 'Unknown' });
  return json({ error: 'Không thể xử lý yêu cầu lúc này.', requestId }, 500);
}
