import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { DatabaseSync } from 'node:sqlite';
import vm from 'node:vm';
import { createWorker } from '../worker/index.js';
import { AdministratorAccount, CustomerAccount } from '../worker/domain/account.js';
import { Booking } from '../worker/domain/booking.js';
import { Departure } from '../worker/domain/departure.js';
import { PaymentEvent } from '../worker/domain/payment-event.js';
import { Tour } from '../worker/domain/tour.js';
import { createSession, customerCookie } from '../worker/service/session.js';
import { makeWorker } from './local-worker.js';

const root = fileURLToPath(new URL('..', import.meta.url));
const date = '2028-04-01';
const input = {
  title: 'Hà Nội', province: 'Hà Nội', place: 'Hồ Gươm',
  desc: 'Thử nghiệm cục bộ', days: 1, itinerary: ['Đi bộ'], price: 1200000,
};
const traveler = { id: 'fixture-customer', name: 'Khách thử', username: 'fixture_customer' };

test('4.1: Xóa tour không có đơn/lịch thì điểm ghé đi theo tour, địa danh dùng chung vẫn còn', async t => {
  const { db } = await makeWorker();
  t.after(() => db.close());
  const writeTour = db.prepare('INSERT INTO tours (id, price, content) VALUES (?, ?, ?)');
  const writeStop = db.prepare('INSERT INTO tour_stops VALUES (?, ?, ?, ?)');
  const location = db.prepare('INSERT INTO destinations (province, name) VALUES (?, ?)').run('Hà Nội', 'Điểm thử 4.1');
  writeTour.run('tour-4a', 1200000, '{}');
  writeTour.run('tour-4b', 1200000, '{}');
  writeStop.run('tour-4a', 1, location.lastInsertRowid, 'Sáng đi bộ');
  writeStop.run('tour-4b', 1, location.lastInsertRowid, 'Tối đi bộ');
  const remove = db.prepare('DELETE FROM tours WHERE id = ?');
  remove.run('tour-4a');
  assert.deepEqual(db.prepare("SELECT tour_id FROM tour_stops WHERE destination_id = ?").all(location.lastInsertRowid).map(row => row.tour_id), ['tour-4b']);
  assert.ok(db.prepare('SELECT id FROM destinations WHERE id = ?').get(location.lastInsertRowid));
  db.prepare('INSERT INTO departures (tour_id, day, capacity) VALUES (?, ?, 5)').run('tour-4b', date);
  assert.throws(() => remove.run('tour-4b'), /FOREIGN KEY/);
  assert.ok(db.prepare('SELECT 1 FROM tour_stops WHERE tour_id = ?').get('tour-4b'));
  assert.deepEqual(db.prepare('PRAGMA foreign_key_check').all(), []);
});

test('4.1: Migration giữ nguyên điểm ghé và khóa ngoại từ cơ sở dữ liệu đang chạy', t => {
  const db = new DatabaseSync(':memory:', { enableForeignKeyConstraints: true });
  t.after(() => db.close());
  const migration = name => readFileSync(resolve(root, 'Database', name), 'utf8');
  for (const name of readdirSync(resolve(root, 'Database')).filter(name => /^000[0-4].*\.sql$/.test(name)).sort()) {
    db.exec(migration(name));
  }
  db.exec(`
    INSERT INTO tours VALUES ('legacy-tour', 100000, 0, '{}');
    INSERT INTO destinations (province, name) VALUES ('Hà Nội', 'Địa danh cũ');
    INSERT INTO tour_stops
    SELECT 'legacy-tour', 1, id, 'Dữ liệu cũ' FROM destinations WHERE name = 'Địa danh cũ';
  `);
  const before = db.prepare('SELECT * FROM tour_stops').all();
  db.exec(migration('0005_tour_stop_ownership.sql'));
  assert.deepEqual(db.prepare('SELECT * FROM tour_stops').all(), before);
  assert.deepEqual(db.prepare('PRAGMA foreign_key_check').all(), []);
});

test('4.3: Không có chu kỳ import, DAL/UI vắng mặt trong BLL và Domain', () => {
  const files = readdirSync(resolve(root, 'worker'), { recursive: true }).filter(path => path.endsWith('.js'));
  const imports = new Map(files.map(path => {
    const source = readFileSync(resolve(root, 'worker', path), 'utf8');
    const deps = Array.from(source.matchAll(/^import.+?from ['"]([^'"]+)['"]/gm), match =>
      relative(resolve(root, 'worker'), resolve(root, 'worker', dirname(path), match[1])));
    if (path.startsWith('domain/') || path.startsWith('service/') || path.startsWith('api/')) {
      for (const dep of deps) assert.doesNotMatch(dep, /^(\.\.|database\/|index\.js$)/, path + ' → ' + dep);
      assert.doesNotMatch(source, /\b(?:SELECT\s+\S+\s+FROM|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM)\b/i, path);
    }
    if (path.startsWith('domain/')) {
      assert.ok(deps.every(dep => dep.startsWith('domain/')), path);
    }
    return [path, deps];
  }));
  const visited = new Set();
  function visit(path, chain) {
    assert.ok(!chain.includes(path), 'Chu kỳ: ' + [...chain, path].join(' → '));
    if (visited.has(path)) return;
    assert.ok(imports.has(path), path + ' nằm ngoài các module Worker');
    for (const dep of imports.get(path)) visit(dep, [...chain, path]);
    visited.add(path);
  }
  for (const path of files) visit(path, []);
});

test('4.4: Bất biến và hợp đồng đa hình của tài khoản', () => {
  const tour = new Tour('fixture-tour', input);
  const copied = [...tour.stops];
  assert.throws(() => tour.stops.push(tour.stops[0]), TypeError);
  copied.pop();
  assert.equal(tour.stops.length, 1);
  assert.throws(() => { tour.stops[0].destination.name = 'Tên khác'; }, TypeError);
  assert.throws(() => { tour.details.days = 2; }, TypeError);
  assert.throws(() => new Tour('fixture', { ...input, days: 2 }), { status: 400 });
  assert.throws(() => new Departure('fixture', date, 3, 4), { status: 400 });
  const booking = new Booking({ adults: 1, children: 2, unitPrice: 1200000 });
  assert.throws(() => { booking.unitPrice = 1; }, TypeError);
  assert.equal(booking.total, 3600000);
  assert.throws(() => new Booking({ adults: 1, children: 0, status: 'pending', paid: true }), { status: 400 });
  assert.throws(() => new PaymentEvent({ date, kind: 'refund', amount: 0 }), { status: 400 });
  const participants = [new CustomerAccount(traveler), new AdministratorAccount('fixture_admin')];
  const getBookingScope = account => account.bookingScope();
  assert.deepEqual(participants.map(getBookingScope), [traveler.id, null]);
  assert.deepEqual(participants.map(account => account.toPublic().role), ['customer', 'admin']);
  assert.throws(() => { participants[0].role = 'admin'; }, TypeError);
});

test('4.5: Thành phần lắp đặt đổi BookingPort sang in-memory ở điểm vào HTTP', async () => {
  const requests = [];
  const accounts = { findPublicById: async id => id === traveler.id ? traveler : null };
  const bookings = {
    async placeBooking(booking, today) {
      requests.push({ booking, today });
      return true;
    },
    async listBookings(ownerId) {
      return requests.filter(item => item.booking.userId === ownerId).map(item => ({ id: item.booking.id }));
    },
    async updateBooking() { return false; },
    async paymentHistory() { return []; },
  };
  const worker = createWorker({
    today: () => date,
    repositories: { accounts: () => accounts, bookings: () => bookings, catalog: () => null, reports: () => null },
  });
  const env = { ADMIN_SESSION_SECRET: crypto.randomUUID() };
  const token = (await createSession(customerCookie, env.ADMIN_SESSION_SECRET, traveler.id)).split(';')[0];
  const origin = 'http://localhost';
  const response = await worker.fetch(new Request(origin + '/api/ops/bookings', {
    method: 'POST', headers: { Origin: origin, Cookie: token },
    body: JSON.stringify({ tourId: 'tour', day: date, name: traveler.name, phone: '0900000000', adults: 1, children: 2 }),
  }), env);
  assert.equal(response.status, 201);
  const { id } = await response.json();
  assert.equal(requests[0].booking.people, 3);
  assert.equal(requests[0].today, date);
  const list = await worker.fetch(new Request(origin + '/api/ops/bookings', { headers: { Cookie: token } }), env);
  assert.deepEqual(await list.json(), { bookings: [{ id }] });
});

test('4.6: Thêm Concrete Strategy mà không sửa Presenter hoặc ba biến thể cũ', () => {
  const context = vm.createContext({ date: day => day.split('-').reverse().join('/') });
  const source = readFileSync(resolve(root, 'dist/report-strategies.js'), 'utf8');
  const result = vm.runInContext(source + `
    class RefundOnlyReport {
      get title() { return 'Chỉ hoàn tiền'; }
      summarize({cash}) {
        return {
          headers: ['Tháng', 'Hoàn tiền (VND)'],
          rows: cash.map(row => [row.month, row.refunded]),
          total: ['Tổng cộng', cash.reduce((sum, row) => sum + row.refunded, 0)],
          note: 'Kỳ lọc tính theo ngày ghi nhận tiền.',
        };
      }
    }
    const extended = new ReportPresenter({cash: new CashReport(), refunds: new RefundOnlyReport()});
    const input = { cash: [{ month: '2028-04', collected: 1200000, refunded: 500000 }] };
    JSON.stringify([
      reportPresenter.options().length, extended.present('cash', input).rows[0],
      extended.present('refunds', input),
    ]);
  `, context);
  assert.deepEqual(JSON.parse(result), [3, ['2028-04', 1200000, 500000, 700000], {
    title: 'Chỉ hoàn tiền', headers: ['Tháng', 'Hoàn tiền (VND)'],
    rows: [['2028-04', 500000]], total: ['Tổng cộng', 500000],
    note: 'Kỳ lọc tính theo ngày ghi nhận tiền.',
  }]);
});
