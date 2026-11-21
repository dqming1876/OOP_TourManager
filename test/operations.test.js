import test from 'node:test';
import assert from 'node:assert/strict';
import { makeWorker } from './local-worker.js';

const origin = 'http://localhost:4173';
const future = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
const tour = {
  title: 'Hà Nội cuối tuần', province: 'Hà Nội', place: 'Hồ Hoàn Kiếm',
  desc: 'Lịch trình trải nghiệm Hà Nội', price: 1200000, days: 2, itinerary: ['Ngày 1', 'Ngày 2'],
};

async function fixture(t) {
  const worker = makeWorker();
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
  const admin = await login(worker.env.ADMIN_USERNAME, worker.env.ADMIN_PASSWORD);
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
