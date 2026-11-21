import { writeFileSync } from 'node:fs';
import { demoSql } from './demo-data.mjs';

const target = process.argv[2];
if (!target?.endsWith('.sql')) {
  console.error('Cách dùng: node scripts/seed-demo.mjs <tệp-demo.sql>');
  process.exit(2);
}
writeFileSync(target, demoSql(), { flag: 'wx' });
console.log('Đã tạo bộ seed. Chỉ nạp vào D1 cục bộ hoặc cơ sở dữ liệu demo.');
