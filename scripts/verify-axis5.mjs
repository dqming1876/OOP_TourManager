import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const scratch = mkdtempSync(join(tmpdir(), 'mingo-axis5-'));
const run = args => {
  const result = spawnSync(process.execPath, args, { cwd: scratch, encoding: 'utf8', timeout: 30000 });
  if (result.error) throw result.error;
  return result;
};
const checkLastSeats = () => run(['--test', '--test-reporter=tap',
  '--test-name-pattern=^IT-01', 'test/integration-axis5.test.js']);

try {
  for (const entry of ['package.json', 'worker', 'Database', 'scripts', 'test']) {
    cpSync(join(root, entry), join(scratch, entry), { recursive: true });
  }
  const repository = join(scratch, 'worker/database/booking-repository.js');
  const original = readFileSync(repository, 'utf8');
  const guard = 'AND d.capacity - d.reserved >= ?';
  const mutant = 'AND d.capacity - d.reserved > ?';
  assert.equal(original.split(guard).length, 2, 'Chỉ thay đúng một guard giữ chỗ');

  const baseline = checkLastSeats();
  assert.equal(baseline.status, 0, baseline.stdout + baseline.stderr);
  assert.match(baseline.stdout, /ok 1 - IT-01/);
  console.log('Baseline >=: IT-01 PASS.');

  writeFileSync(repository, original.replace(guard, mutant));
  const failed = checkLastSeats();
  assert.equal(failed.status, 1, failed.stdout + failed.stderr);
  assert.match(failed.stdout, /not ok 1 - IT-01/);
  assert.match(failed.stdout, /Ba khách phải đặt được khi đợt còn đúng ba chỗ/);
  assert.match(failed.stdout, /409 !== 201/);
  console.log('Mutant >: IT-01 FAIL vì 409 thay cho 201.');

  const debug = run(['scripts/debug-axis5.mjs', '409']);
  assert.equal(debug.status, 0, debug.stdout + debug.stderr);
  process.stdout.write(debug.stdout);

  writeFileSync(repository, original);
  const restored = checkLastSeats();
  assert.equal(restored.status, 0, restored.stdout + restored.stderr);
  assert.match(restored.stdout, /ok 1 - IT-01/);
  console.log('Khôi phục >=: IT-01 PASS.');
} finally {
  rmSync(scratch, { recursive: true, force: true });
}
