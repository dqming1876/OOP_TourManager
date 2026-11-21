import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Session } from 'node:inspector';
import { makeWorker } from './sqlite-worker.mjs';

const points = [
  ['tour-stop', '../worker/domain/tour.js', 'return new TourStop(index', 'index + 1', ['Tour', 'saveTour']],
  ['place-booking', '../worker/service/booking-service.js', 'if (!await this.repository.placeBooking',
    'booking.people', ['placeBooking', 'operationsRoute']],
  ['hold-seats', '../worker/database/booking-repository.js', 'INSERT INTO bookings (id,user_id',
    'people', ['placeBooking', 'operationsRoute']],
  ['payment-guard', '../worker/database/booking-repository.js', 'UPDATE bookings SET status = ?',
    '[rule.from, rule.alsoFrom, rule.nextPaid, ownerId === null]', ['updateBooking', 'operationsRoute']],
];

const session = new Session();
session.connect();
const post = (method, parameters) => new Promise((resolve, reject) => {
  session.post(method, parameters, (error, data) => error ? reject(error) : resolve(data));
});
const breakpoints = new Map();
const records = [];
const debuggerErrors = [];

session.on('Debugger.paused', ({ params }) => {
  const point = breakpoints.get(params.hitBreakpoints[0]);
  if (!point) {
    session.post('Debugger.resume');
    return;
  }
  const [label, , , expression, expected] = point;
  const stack = params.callFrames.map(frame => frame.functionName).filter(Boolean);
  session.post('Debugger.evaluateOnCallFrame', {
    callFrameId: params.callFrames[0].callFrameId, expression, returnByValue: true,
  }, (error, response) => {
    if (error || response.exceptionDetails) debuggerErrors.push(label + ': không đọc được Watch');
    else records.push({ label, stack, watch: response.result.value, expected });
    session.post('Debugger.resume');
  });
});

let db;
try {
  await post('Debugger.enable');
  for (const point of points) {
    const [, path, needle] = point;
    const url = new URL(path, import.meta.url);
    const lines = readFileSync(url, 'utf8').split('\n');
    const found = lines.findIndex(line => line.includes(needle));
    assert.notEqual(found, -1, needle);
    // For the SQL template, suspend on the beginning of the statement.
    const lineNumber = ['hold-seats', 'payment-guard'].includes(point[0]) ? found - 1 : found;
    const { breakpointId, locations } = await post('Debugger.setBreakpointByUrl', { url: url.href, lineNumber });
    assert.equal(locations.length, 1, url.href);
    breakpoints.set(breakpointId, point);
  }

  const fixture = await makeWorker();
  db = fixture.db;
  const origin = 'http://localhost';
  const day = new Date(Date.now() + 10 * 86400000).toISOString().slice(0, 10);
  const send = (path, body, cookie = '') => fixture.fetch(new Request(origin + '/api/' + path, {
    method: 'POST', headers: { Origin: origin, Cookie: cookie }, body: JSON.stringify(body),
  }));
  const cookie = response => response.headers.getSetCookie().find(value => !value.includes('Max-Age=0')).split(';')[0];

  const admin = cookie(await send('auth/login', { username: fixture.env.ADMIN_USERNAME, password: fixture.adminPassword }));
  const profile = { name: 'Khách thử', username: 'debug_guest', password: crypto.randomUUID() };
  assert.equal((await send('auth/register', profile)).status, 201);
  const guest = cookie(await send('auth/login', profile));
  const tour = await send('ops/tours', {
    title: 'Tour thử', province: 'Hà Nội', place: 'Hồ Gươm', days: 2,
    itinerary: ['Đi bộ', 'Tham quan'], desc: 'Kiểm thử debugger', price: 1200000,
  }, admin);
  assert.equal(tour.status, 201);
  const { id: tourId } = await tour.json();
  assert.equal((await send('ops/tours/' + tourId + '/departures', { day, capacity: 3 }, admin)).status, 200);
  const booking = await send('ops/bookings', { tourId, day, name: profile.name,
    phone: '0900000000', adults: 2, children: 1 }, guest);
  assert.equal(booking.status, 201);
  const { id } = await booking.json();
  // A pending order cannot be collected. Direct HTTP uses the same guard as the Form.
  assert.equal((await send('ops/bookings/' + id + '/collect', {}, admin)).status, 409);
  assert.equal(db.prepare('SELECT paid FROM bookings WHERE id = ?').get(id).paid, 0);
  assert.equal(db.prepare('SELECT COUNT(*) AS count FROM payment_events WHERE booking_id = ?').get(id).count, 0);

  assert.deepEqual(debuggerErrors, []);
  assert.deepEqual(records.map(row => [row.label, row.watch]), [
    ['tour-stop', 1], ['tour-stop', 2], ['place-booking', 3], ['hold-seats', 3],
    ['payment-guard', ['confirmed', null, true, true]],
  ]);
  for (const { label, stack, watch, expected } of records) {
    for (const frame of expected) assert.ok(stack.includes(frame), label + ': ' + stack.join(' → '));
    console.log(label + ' | ' + stack.slice(0, 6).join(' → ') + ' | Watch ' + JSON.stringify(watch));
  }
  console.log('HTTP 409 khi thu đơn chờ; paid = 0, bút toán = 0.');
} finally {
  session.disconnect();
  db?.close();
}
