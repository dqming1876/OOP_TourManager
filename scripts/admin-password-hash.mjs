import { randomUUID } from 'node:crypto';
import { passwordHash } from '../worker/service/passwords.js';

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const password = Buffer.concat(chunks).toString('utf8').replace(/\r?\n$/, '');
if (password.length < 12 || password.length > 128) {
  console.error('Nhập mật khẩu quản trị dài 12–128 ký tự qua stdin.');
  process.exitCode = 1;
} else {
  const salt = randomUUID();
  console.log('ADMIN_PASSWORD_SALT=' + salt);
  console.log('ADMIN_PASSWORD_HASH=' + await passwordHash(password, salt));
}
