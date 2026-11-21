import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Session } from 'node:inspector';
import { lastSeatsFixture } from '../test/fixtures/axis5.js';

const repository = new URL('../worker/database/booking-repository.js', import.meta.url);
const lines = readFileSync(repository, 'utf8').split('\n');
const guard = lines.find(line => line.includes('AND d.capacity - d.reserved'));
const placeBookingLine = lines.findIndex((line, index) =>
  line.includes('const result = await this.prepare') && lines[index + 1].includes('INSERT INTO bookings'));
assert.ok(guard && placeBookingLine >= 0);

const session = new Session();
session.connect();
const post = (method, parameters) => new Promise((resolve, reject) => {
  session.post(method, parameters, (error, value) => error ? reject(error) : resolve(value));
});

let observation;
let missedWatch;
session.on('Debugger.paused', ({ params }) => {
  const stack = params.callFrames.map(frame => frame.functionName).filter(Boolean);
  session.post('Debugger.evaluateOnCallFrame', {
    callFrameId: params.callFrames[0].callFrameId,
    expression: `(() => {
      const departure = this.db.database.prepare('SELECT capacity, reserved FROM departures WHERE tour_id = ? AND day = ?').get(tourId, day);
      return { requested: people, capacity: departure.capacity, reserved: departure.reserved };
    })()`,
    returnByValue: true,
  }, (error, result) => {
    if (error || result.exceptionDetails) missedWatch = true;
    else observation = { stack, watch: result.result.value };
    session.post('Debugger.resume');
  });
});

let fixture;
try {
  await post('Debugger.enable');
  const breakpoint = await post('Debugger.setBreakpointByUrl', {
    url: repository.href, lineNumber: placeBookingLine,
  });
  assert.equal(breakpoint.locations.length, 1);
  fixture = await lastSeatsFixture();
  const response = await fixture.placeBooking();
  assert.ok(observation && !missedWatch, 'Breakpoint phải có giá trị Watch thực');
  assert.deepEqual(observation.stack.slice(0, 3), ['placeBooking', 'placeBooking', 'operationsRoute']);
  assert.deepEqual(observation.watch, { requested: 3, capacity: 3, reserved: 0 });
  const expectedStatus = Number(process.argv[2] ?? '201');
  assert.equal(response.status, expectedStatus);
  console.log('Call Stack: BookingRepository.' + observation.stack[0] + ' → BookingService.' +
    observation.stack[1] + ' → ' + observation.stack[2]);
  console.log('Watch: ' + JSON.stringify(observation.watch) + ' → available = 3.');
  console.log('Guard: ' + guard.trim() + ' → HTTP ' + response.status + '.');
} finally {
  session.disconnect();
  fixture?.db.close();
}
