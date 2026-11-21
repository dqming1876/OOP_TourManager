import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const path = process.argv[2];
if (!path?.endsWith('.zip')) {
  console.error('Cách dùng: node scripts/package-demo.mjs <mingo-demo.zip>');
  process.exit(2);
}
const output = resolve(path);
if (existsSync(output)) {
  console.error('Tệp ZIP đã tồn tại:', output);
  process.exit(2);
}
const result = spawnSync('zip', [
  '-q', '-r', output, 'dist', 'drizzle', 'worker', 'scripts', 'test', 'docs',
  'package.json', 'README.md', 'wrangler.jsonc', '.gitignore',
  '-x', 'dist/server/*', '*/.DS_Store',
], { stdio: 'inherit' });
if (result.error || result.status !== 0) {
  console.error(result.error?.message || 'Không tạo được ZIP.');
  process.exit(1);
}
console.log(output);
