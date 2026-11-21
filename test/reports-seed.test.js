import test from 'node:test';
import assert from 'node:assert/strict';
import { makeWorker } from './local-worker.js';
import { demoSql, demoCustomerPassword } from '../scripts/demo-data.mjs';

test('Seed tạo 126 đơn liên thông và số liệu báo cáo khớp tính tay', async t => {
  const now = new Date();
  const { db, env, adminPassword, fetch } = await makeWorker({ seed: demoSql(now) });
  t.after(() => db.close());
  const queries = {
    accounts: "SELECT COUNT(*) FROM accounts WHERE id LIKE 'demo-%'",
    tours: "SELECT COUNT(*) FROM tours WHERE id LIKE 'demo-%'",
    destinations: 'SELECT COUNT(DISTINCT destination_id) FROM tour_stops',
    tour_stops: 'SELECT COUNT(*) FROM tour_stops',
    departures: "SELECT COUNT(*) FROM departures WHERE tour_id LIKE 'demo-%'",
    bookings: 'SELECT COUNT(*) FROM bookings',
    payment_events: 'SELECT COUNT(*) FROM payment_events',
  };
  assert.deepEqual(Object.fromEntries(Object.entries(queries).map(([key, sql]) =>
    [key, db.prepare(sql).get()['COUNT(*)'] ?? db.prepare(sql).get()['COUNT(DISTINCT destination_id)']],
  )), { accounts: 8, tours: 3, destinations: 6, tour_stops: 6, departures: 18, bookings: 126, payment_events: 69 });
  assert.deepEqual(db.prepare('PRAGMA foreign_key_check').all(), []);

  const origin = 'http://localhost';
  const login = async (username, password) => {
    const response = await fetch(new Request(origin + '/api/auth/login', {
      method: 'POST', headers: { Origin: origin }, body: JSON.stringify({ username, password }),
    }));
    assert.equal(response.status, 200);
    return response.headers.getSetCookie().find(c => !c.includes('Max-Age=0')).split(';')[0];
  };
  const admin = await login(env.ADMIN_USERNAME, adminPassword);
  const customer = await login('mingo_khach1', demoCustomerPassword);
  const listBookings = async cookie => {
    const response = await fetch(new Request(origin + '/api/ops/bookings', { headers: { Cookie: cookie } }));
    assert.equal(response.status, 200);
    return (await response.json()).bookings;
  };
  assert.equal((await listBookings(admin)).length, 126);
  const ownBookings = await listBookings(customer);
  assert.equal(ownBookings.length, 11);
  assert.ok(ownBookings.every(booking => booking.name === 'Nguyễn An'));
  const [y,m] = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' }).format(now).split('-').map(Number);
  const month = offset => new Date(Date.UTC(y, m - 1 + offset, 1)).toISOString().slice(0,7);
  const report = (cookie, args) => fetch(new Request(origin + '/api/ops/reports?' + new URLSearchParams(args), {
    headers: { Cookie: cookie },
  }));

  const historical = { from: month(-1) + '-01', to: month(-1) + '-28', tour: 'demo-hanoi' };
  const filtered = await (await report(admin, historical)).json();
  assert.deepEqual(filtered.cash, [{ month: month(-1), collected: 3600000, refunded: 1200000 }]);
  assert.deepEqual(Object.fromEntries(filtered.bookings.map(row => [row.state, row.guests])),
    { cancelled: 1, completed: 2, confirmed: 2, expired: 2 });
  assert.deepEqual(filtered.capacity.map(({ capacity, reserved, available }) => ({ capacity, reserved, available })),
    [{ capacity: 8, reserved: 6, available: 2 }]);
  const all = await (await report(admin, { tour: 'demo-hanoi' })).json();
  assert.deepEqual(all.cash, [
    { month: month(-3), collected: 14400000, refunded: 1200000 },
    { month: month(-2), collected: 3600000, refunded: 1200000 },
    { month: month(-1), collected: 3600000, refunded: 1200000 },
    { month: month(0), collected: 28800000, refunded: 2400000 },
    { month: month(1), collected: 3600000, refunded: 0 },
  ]);
  assert.deepEqual(all.capacity.map(row => row.available), [6, 2, 2, 4, 1, 0]);
  const expanded = await (await report(admin, { ...historical, from: month(-3) + '-01', to: month(-3) + '-28' })).json();
  assert.deepEqual(Object.fromEntries(expanded.bookings.map(row => [row.state, row.guests])),
    { cancelled: 3, completed: 11, confirmed: 6, expired: 7 });
  assert.equal((await report(customer,historical)).status,403);
  assert.equal((await report(admin,{from:'2026-11-30',to:'2026-11-01'})).status,400);
});

test('Phiếu thu và hoàn xuất hiện ngay trên báo cáo và chi tiết đơn', async t => {
  const { env, db, adminPassword, fetch } = await makeWorker({ seed: demoSql() });
  t.after(() => db.close());
  const origin = 'http://localhost';
  async function request(path, body, cookie) {
    return fetch(new Request(origin + '/api/' + path, body ? {
      method: 'POST', headers: { Origin: origin, Cookie: cookie || '' }, body: JSON.stringify(body),
    } : { headers: { Cookie: cookie || '' } }));
  }
  const loggedIn = await request('auth/login', { username: env.ADMIN_USERNAME, password: adminPassword });
  const cookie = loggedIn.headers.getSetCookie().find(c => c.startsWith('dv_admin=')).split(';')[0];
  const id = 'MGDEMO023'; // Hà Nội, kỳ tương lai, đơn xác nhận chưa thu, 2 khách.
  const today = new Intl.DateTimeFormat('sv-SE', { timeZone:'Asia/Ho_Chi_Minh' }).format(new Date());
  const report = async () => {
    const { cash } = await (await request('ops/reports?tour=demo-hanoi&from='+today+'&to='+today, null, cookie)).json();
    return cash[0] ?? { month: today.slice(0,7), collected: 0, refunded: 0 };
  };
  const before = await report();
  const collected = before.collected + 2400000;
  assert.equal((await request('ops/bookings/'+id+'/collect', {}, cookie)).status, 200);
  assert.deepEqual(await report(), { ...before, collected });
  assert.equal((await request('ops/bookings/'+id+'/refund', {}, cookie)).status, 200);
  assert.deepEqual(await report(), { ...before, collected, refunded: before.refunded + 2400000 });
  const history = await (await request('ops/bookings/'+id+'/payments', null, cookie)).json();
  assert.deepEqual(history.payments.map(p => [p.kind,p.amount]), [['collect',2400000],['refund',2400000]]);
  assert.deepEqual(history.payments.map(p => p.signedAmount), [2400000, -2400000]);
});
