import test from 'node:test';
import assert from 'node:assert/strict';
import { pbkdf2Sync } from 'node:crypto';
import { makeWorker } from './local-worker.js';
import { AdministratorAccount, CustomerAccount } from '../worker/domain/account.js';
import { BookingRepository } from '../worker/database/booking-repository.js';
import { AccessPolicy } from '../worker/service/access-policy.js';
import { BookingService } from '../worker/service/booking-service.js';
import { TourCatalogService } from '../worker/service/tour-catalog-service.js';

const origin = 'http://localhost:4173';
const future = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
const tour = {
  title: 'Hà Nội cuối tuần', province: 'Hà Nội', place: 'Hồ Hoàn Kiếm',
  desc: 'Lịch trình trải nghiệm Hà Nội', price: 1200000, days: 2, itinerary: ['Ngày 1', 'Ngày 2'],
};

async function fixture(t) {
  const worker = await makeWorker();
  t.after(() => worker.db.close());
  async function request(path, body, cookie) {
    const headers = { Origin: origin, ...(cookie ? { Cookie: cookie } : {}) };
    const response = await worker.fetch(new Request(origin + '/api/' + path, body === undefined ? { headers } : {
      method: 'POST', headers, body: JSON.stringify(body),
    }));
    return { status: response.status, data: await response.json(), cookies: response.headers.getSetCookie() };
  }
  async function login(username, password) {
    const result = await request('auth/login', { username, password });
    assert.equal(result.status, 200);
    return result.cookies.find(cookie => !cookie.includes('Max-Age=0')).split(';')[0];
  }
  async function customer(username) {
    assert.equal((await request('auth/register', { name: username, username, password: 'fixture-only' })).status, 201);
    return login(username, 'fixture-only');
  }
  const admin = await login(worker.env.ADMIN_USERNAME, worker.adminPassword);
  const a = await customer('demo_a');
  const b = await customer('demo_b');
  const created = await request('ops/tours', tour, admin);
  assert.equal(created.status, 201);
  const tourId = created.data.id;
  const schedule = 'ops/tours/' + tourId + '/departures';
  assert.equal((await request(schedule, { day: future, capacity: 3 }, admin)).status, 200);
  return { ...worker, request, admin, a, b, tourId, schedule };
}

function details(tourId, adults = 2) {
  return { tourId, day: future, adults, children: 1, name: 'Khách mẫu', phone: '0900000000' };
}

test('Giữ chỗ và trả chỗ: khách độc lập thấy cùng sức chứa, đơn chỉ thuộc người đặt', async t => {
  const { request, a, b, admin, tourId, schedule } = await fixture(t);
  const [aOrder, bOrder] = await Promise.all([
    request('ops/bookings', details(tourId), a),
    request('ops/bookings', details(tourId), b),
  ]);
  assert.deepEqual([aOrder.status,bOrder.status].sort(), [201,409]);
  const [owner, other, id] = aOrder.status === 201 ? [a, b, aOrder.data.id] : [b, a, bOrder.data.id];
  assert.equal((await request('ops/bookings', undefined, other)).data.bookings.length, 0);
  assert.equal((await request('ops/bookings', undefined, admin)).data.bookings[0].total, 3600000);
  const available = async () => (await request('ops/tours')).data.tours.find(tour => tour.id === tourId).departures[0].remaining;
  assert.equal(await available(), 0);
  assert.equal((await request(schedule, { day: future, capacity: 2, edit: true }, admin)).status, 409);
  assert.equal((await request('ops/bookings/' + id + '/cancel', {}, other)).status, 409);
  assert.equal(await available(), 0);
  assert.equal((await request('ops/bookings/' + id + '/cancel', {}, owner)).status, 200);
  assert.equal((await request('ops/bookings/' + id + '/cancel', {}, owner)).status, 409);
  assert.equal(await available(), 3);
  assert.equal((await request('ops/tours/' + tourId + '/remove-departure', { day: future }, admin)).status, 409);
});

test('Phân quyền và trạng thái: quản trị xác nhận, thu, hoàn và hủy', async t => {
  const { request, admin, a, tourId, schedule } = await fixture(t);
  assert.equal((await request('ops/tours', tour)).status, 401);
  assert.equal((await request('ops/tours', tour, a)).status, 403);
  assert.equal((await request(schedule, { day: future, capacity: 5 }, a)).status, 403);
  assert.equal((await request('ops/bookings', details(tourId), admin)).status, 403);
  assert.equal((await request('ops/bookings', { ...details(tourId), day: '2028-02-31' }, a)).status, 400);
  const created = await request('ops/bookings', details(tourId), a);
  assert.equal(created.status, 201);
  const id = created.data.id;
  const action = (verb, cookie = admin) => request('ops/bookings/' + id + '/' + verb, {}, cookie);
  assert.equal((await action('confirm', a)).status, 403);
  assert.equal((await action('collect')).status, 409);
  assert.equal((await action('confirm')).status, 200);
  assert.equal((await action('cancel', a)).status, 409);
  assert.equal((await action('collect')).status, 200);
  assert.equal((await action('collect')).status, 409);
  assert.equal((await action('cancel')).status, 409);
  assert.equal((await request('ops/tours/' + tourId, { ...tour, price: 5000000 }, admin)).status, 200);
  assert.equal((await request('ops/bookings', undefined, a)).data.bookings[0].total, 3600000);
  assert.equal((await action('refund')).status, 200);
  assert.equal((await action('cancel')).status, 200);
  assert.equal((await action('confirm')).status, 409);
  assert.equal((await request('ops/tours/' + tourId + '/visibility', { hidden: true }, admin)).status, 200);
  assert.equal((await request('ops/bookings', details(tourId), a)).status, 409);
  assert.equal((await request('ops/tours')).data.tours.some(tour => tour.id === tourId), false);
});

test('Lỗi khi cập nhật sức chứa khiến việc tạo đơn được hoàn tác', async t => {
  const { request, db, a, tourId } = await fixture(t);
  db.exec(`
    CREATE TRIGGER injected_failure BEFORE UPDATE OF reserved ON departures
    BEGIN SELECT RAISE(ABORT, 'test failure'); END
  `);
  assert.equal((await request('ops/bookings', details(tourId), a)).status, 500);
  assert.equal(db.prepare('SELECT count(*) AS count FROM bookings').get().count, 0);
  assert.equal(db.prepare('SELECT reserved FROM departures WHERE tour_id = ? AND day = ?').get(tourId, future).reserved, 0);
});

test('Validation Worker trả đúng ô lỗi trước khi ghi tour, lịch, đơn và hồ sơ', async t => {
  const { request, admin, a, tourId, schedule } = await fixture(t);
  const cases = [
    ['ops/tours', { ...tour, title: '  ' }, admin, 'title'],
    ['ops/tours/' + tourId, { ...tour, price: 1.5 }, admin, 'price'],
    ['ops/tours', { ...tour, itinerary: ['Ngày 1', ' '] }, admin, 'itinerary-1'],
    [schedule, { day: '2000-01-01', capacity: 3 }, admin, 'day'],
    [schedule, { day: future, capacity: 101 }, admin, 'capacity'],
    ['ops/bookings', { ...details(tourId), adults: 0 }, a, 'adults'],
    ['ops/bookings', { ...details(tourId), phone: '12345678xx' }, a, 'phone'],
    ['profile', { name: 'Khách mẫu', birthday: '2024-02-30' }, a, 'birthday'],
    ['profile', { name: 'Khách mẫu', phone: 'abc' }, a, 'phone'],
  ];
  for (const [path, body, cookie, field] of cases) {
    const { status, data } = await request(path, body, cookie);
    assert.equal(status, 400, path + ' ' + field);
    assert.equal(data.field, field, path);
  }
  const duplicate = await request(schedule, { day: future, capacity: 12 }, admin);
  assert.equal(duplicate.status, 409);
  assert.equal(duplicate.data.field, 'day');
  const available = async () => (await request('ops/tours')).data.tours.find(t => t.id === tourId).departures[0].remaining;
  assert.equal(await available(), 3);
  assert.equal((await request(schedule, { day: future, capacity: 4, edit: true }, admin)).status, 200);
  assert.equal(await available(), 4);
  assert.equal((await request('ops/bookings', { ...details(tourId), adults: 5 }, a)).data.field, 'day');
  assert.equal((await request('ops/bookings', undefined, a)).data.bookings.length, 0);
  const saved = await request('profile', { name: 'Khách mẫu', phone: '0900000000', birthday: '2024-02-29' }, a);
  assert.equal(saved.status, 200);
  assert.equal(saved.data.user.birthday, '2024-02-29');
});

test('Lỗi giữa lúc trả chỗ giữ nguyên trạng thái đơn và sức chứa', async t => {
  const { request, db, a, tourId } = await fixture(t);
  const order = await request('ops/bookings', details(tourId), a);
  assert.equal(order.status, 201);
  db.exec(`
    CREATE TRIGGER fixture_cancel_failure BEFORE UPDATE OF reserved ON departures
    BEGIN SELECT RAISE(ABORT, 'fixture internal details'); END
  `);
  const failed = await request('ops/bookings/' + order.data.id + '/cancel', {}, a);
  assert.equal(failed.status, 500);
  assert.deepEqual(Object.keys(failed.data).sort(), ['error', 'requestId']);
  assert.match(failed.data.requestId, /^[0-9a-f-]{36}$/);
  assert.doesNotMatch(JSON.stringify(failed.data), /fixture internal details|stack/i);
  assert.equal(db.prepare('SELECT status FROM bookings WHERE id = ?').get(order.data.id).status, 'pending');
  assert.equal(db.prepare('SELECT reserved FROM departures WHERE tour_id = ? AND day = ?').get(tourId, future).reserved, 3);
});

test('Tài khoản giữ hash có salt, đăng nhập quản trị bằng hash cấu hình', async t => {
  const { request, db, env, adminPassword, a } = await fixture(t);
  const accounts = db.prepare('SELECT password_hash, salt FROM accounts ORDER BY username').all();
  assert.equal(accounts.length, 2);
  for (const account of accounts) assert.match(account.password_hash, /^[a-f0-9]{64}$/);
  assert.notEqual(accounts[0].salt, accounts[1].salt);
  assert.notEqual(accounts[0].password_hash, accounts[1].password_hash);
  const info = await request('auth/me', undefined, a);
  assert.equal(info.data.user.role, 'customer');
  assert.equal('password_hash' in info.data.user, false);
  assert.equal('salt' in info.data.user, false);
  assert.equal((await request('auth/login', { username: env.ADMIN_USERNAME, password: 'incorrect-fixture' })).status, 401);
  assert.equal((await request('admin/login', { username: env.ADMIN_USERNAME, password: adminPassword })).status, 200);
  const legacyAdmin = env.ADMIN_PASSWORD_HASH;
  delete env.ADMIN_PASSWORD_HASH;
  assert.equal((await request('auth/login', { username: env.ADMIN_USERNAME, password: adminPassword })).status, 503);
  env.ADMIN_PASSWORD_HASH = legacyAdmin;

  const oldHash = pbkdf2Sync('old-fixture-password', 'old-fixture-salt', 100000, 32, 'sha256').toString('hex');
  db.prepare('INSERT INTO accounts (id, username, name, password_hash, salt) VALUES (?, ?, ?, ?, ?)')
    .run('old-id', 'old_account', 'Khách cũ', oldHash, 'old-fixture-salt');
  assert.equal((await request('auth/login', { username: 'old_account', password: 'old-fixture-password' })).status, 200);
  const badBody = await request('auth/login', null);
  assert.equal(badBody.status, 400);
});

test('Báo cáo lọc 120 đơn theo ngày và tour bằng ba truy vấn cố định', async t => {
  const { request, db, admin, a, tourId, queries } = await fixture(t);
  const ownerId = db.prepare('SELECT id FROM accounts WHERE username = ?').get('demo_a').id;
  const days = [14, 15].map(offset => new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10));
  const insertDay = db.prepare('INSERT INTO departures (tour_id, day, capacity) VALUES (?, ?, ?)');
  const insertOrder = db.prepare(`
    INSERT INTO bookings (id, user_id, tour_id, day, title, name, phone, adults, children, unit_price, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 1200000, ?)
  `);
  for (const [offset, day] of days.entries()) {
    insertDay.run(tourId, day, 60);
    for (let index = 0; index < 60; index++) {
      insertOrder.run('bench-' + offset + '-' + index, ownerId, tourId, day, 'Tour', 'Khách mẫu',
        '0900000000', offset ? 'confirmed' : 'pending');
    }
  }
  assert.equal((await request('ops/reports', undefined, a)).status, 403);
  assert.equal((await request('ops/reports?from=2028-02-30', undefined, admin)).status, 400);
  const start = queries.length;
  const report = await request('ops/reports', undefined, admin);
  assert.equal(report.data.bookings.reduce((total, row) => total + row.orders, 0), 120);
  const prepared = queries.slice(start);
  assert.equal(prepared.length, 3);
  const bookingPlan = db.prepare('EXPLAIN QUERY PLAN ' + prepared[1]).all(future, future, ...days, '', '');
  assert.ok(bookingPlan.some(step => step.detail.includes('bookings_report_by_day')));
  const day = days[1];
  const durations = [];
  for (let run = 0; run < 30; run++) {
    const begin = performance.now();
    const filtered = await request('ops/reports?from=' + day + '&to=' + day + '&tour=' + tourId, undefined, admin);
    durations.push(performance.now() - begin);
    assert.deepEqual(filtered.data.bookings, [{ month: day.slice(0, 7), state: 'confirmed', orders: 60, guests: 60 }]);
    assert.equal(filtered.data.capacity[0].available, 0);
  }
  durations.sort((first, second) => first - second);
  const p95 = durations[Math.ceil(durations.length * 0.95) - 1];
  t.diagnostic('120 đơn, 30 lượt lọc tại Worker/SQLite cục bộ, P95 = ' + p95.toFixed(2) + ' ms (không gồm mạng/UI).');
});

test('Rollback phiếu thu nếu lỗi khi ghi sổ thanh toán', async t => {
  const { request, db, a, admin, tourId } = await fixture(t);
  const order = await request('ops/bookings', details(tourId), a);
  assert.equal(order.status, 201);
  const path = 'ops/bookings/' + order.data.id;
  assert.equal((await request(path + '/confirm', {}, admin)).status, 200);
  db.exec(`
    CREATE TRIGGER fixture_payment_failure BEFORE INSERT ON payment_events
    BEGIN SELECT RAISE(ABORT, 'fixture payment failure'); END
  `);
  const result = await request(path + '/collect', {}, admin);
  assert.equal(result.status, 500);
  assert.equal(db.prepare('SELECT paid FROM bookings WHERE id = ?').get(order.data.id).paid, 0);
  assert.deepEqual((await request(path + '/payments', undefined, admin)).data.payments, []);
});

test('Trục 3: Service chặn sai vai trò trước khi đọc hoặc ghi vào repository', async () => {
  const denied = error => error.status === 403;
  const guest = new CustomerAccount({ id: 'customer-a', name: 'A', username: 'customer_a' });
  const today = '2026-11-21';
  const guestAccess = new AccessPolicy(guest);
  const guestBookings = new BookingService(null, guestAccess, today);
  const guestCatalog = new TourCatalogService(null, guestAccess, today);
  const asAdmin = new BookingService(null, new AccessPolicy(new AdministratorAccount('admin')), today);
  await assert.rejects(() => guestCatalog.saveTour(null, tour), denied);
  await assert.rejects(() => guestCatalog.saveDeparture('tour', { day: future, capacity: 3 }), denied);
  await assert.rejects(() => guestBookings.updateBooking('order', 'confirm'), denied);
  assert.throws(() => guestBookings.paymentHistory('order'), denied);
  await assert.rejects(() => asAdmin.placeBooking(details('tour')), denied);
  const anonymous = new BookingService(null, new AccessPolicy(null), today);
  assert.throws(() => anonymous.bookings(), { status: 401 });
});

test('Trục 3: Phiếu quá hạn bị từ chối xác nhận tại Service và HTTP', async t => {
  const { request, db, env, admin, a, tourId } = await fixture(t);
  const created = await request('ops/bookings', details(tourId), a);
  assert.equal(created.status, 201);
  const order = created.data.id;
  const adminService = new BookingService(new BookingRepository(env.DB),
    new AccessPolicy(new AdministratorAccount('demo_admin')), '9999-12-31');
  await assert.rejects(() => adminService.updateBooking(order, 'confirm'), { status: 409 });
  assert.equal(db.prepare('SELECT status FROM bookings WHERE id = ?').get(order).status, 'pending');

  const past = '2000-01-01';
  const ownerId = db.prepare('SELECT user_id FROM bookings WHERE id = ?').get(order).user_id;
  db.prepare('INSERT INTO departures (tour_id, day, capacity) VALUES (?, ?, 3)').run(tourId, past);
  db.prepare(`
    INSERT INTO bookings (id, user_id, tour_id, day, title, name, phone, adults, children, unit_price)
    VALUES ('past-fixture', ?, ?, ?, 'Tour', 'Người đặt thử', '0900000000', 1, 0, 1200000)
  `).run(ownerId, tourId, past);
  assert.equal((await request('ops/bookings/past-fixture/confirm', {}, admin)).status, 409);
  assert.equal(db.prepare('SELECT reserved FROM departures WHERE tour_id = ? AND day = ?').get(tourId, past).reserved, 1);
  assert.equal((await request('ops/bookings/past-fixture/cancel', {}, admin)).status, 200);
  assert.equal(db.prepare('SELECT reserved FROM departures WHERE tour_id = ? AND day = ?').get(tourId, past).reserved, 0);
});

test('Trục 3: Điểm đến dùng lại giữa nhiều tour, thuộc tính ngày và hoạt động theo từng liên kết', async t => {
  const { request, db, admin, tourId } = await fixture(t);
  const second = await request('ops/tours', {
    ...tour, title: 'Tour thứ hai', itinerary: ['Tham quan bảo tàng', 'Đi bộ ven hồ'],
    stops: ['Bảo tàng Hà Nội', tour.place],
  }, admin);
  assert.equal(second.status, 201);
  const points = db.prepare(`
    SELECT s.tour_id, s.day_number, s.activity, s.destination_id
    FROM tour_stops s JOIN destinations d ON s.destination_id = d.id
    WHERE s.tour_id IN (?, ?) AND d.name = ? ORDER BY s.day_number, s.tour_id
  `).all(tourId, second.data.id, tour.place);
  assert.equal(points.length, 3);
  assert.equal(new Set(points.map(row => row.destination_id)).size, 1);
  assert.equal(points.find(row => row.tour_id === second.data.id && row.day_number === 2).activity, 'Đi bộ ven hồ');
});
