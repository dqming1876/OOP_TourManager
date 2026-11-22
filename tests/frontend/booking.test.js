import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../../dist/operations.js', import.meta.url), 'utf8')
  .split("window.addEventListener('hashchange'")[0];

test('Only open departures in Vietnam calendar are selectable', async () => {
  const context = vm.createContext({
    user: null, tours: [], bookings: [], Intl, Date,
    fetch: async () => ({ ok: true, json: async () => ({ tours: [{ id: 't', departures: [
      { day: '2028-03-06', remaining: 10 }, { day: '2028-03-07', remaining: 0 },
      { day: '2028-03-07', remaining: 2 }, { day: '2028-03-08', remaining: 5 },
    ] }] }) }),
  });
  vm.runInContext(source, context);
  assert.equal(vm.runInContext("vietnamDay(new Date('2028-03-06T17:00:00Z'))", context), '2028-03-07');
  vm.runInContext("vietnamDay = () => '2028-03-07'", context);
  await vm.runInContext('refreshOperations()', context);
  assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(tours[0].dates)', context)), ['2028-03-07', '2028-03-08']);
});

test('Network retry keeps intent key and displayed price; changed form creates new key', async () => {
  const sent = [];
  const button = { disabled: false };
  const fields = { day: '2028-03-07', adults: '1', children: '0', name: 'Guest', phone: '0900000000' };
  const form = { dataset: { price: '500000' }, querySelector: s => s.includes('button') ? button : {} };
  let key = 0;
  const context = vm.createContext({
    user: { id: 'guest', role: 'customer' }, tours: [{ id: 't', price: 600000 }],
    FormData: class { get(key) { return fields[key]; } },
    crypto: { randomUUID: () => `intent-${++key}` }, remaining: () => 10,
    validateMingoForm: () => true, showSubmissionError: () => {},
    fetch: async (_url, options) => { sent.push(JSON.parse(options.body)); throw Error('offline'); },
    event: { preventDefault() {}, currentTarget: form },
  });
  vm.runInContext(source, context);
  await vm.runInContext("placeOrder(event, 't')", context);
  await vm.runInContext("placeOrder(event, 't')", context);
  fields.adults = '2';
  await vm.runInContext("placeOrder(event, 't')", context);
  assert.equal(sent[0].expectedPrice, 500000);
  assert.equal(sent[0].requestId, sent[1].requestId);
  assert.notEqual(sent[1].requestId, sent[2].requestId);
  assert.equal(button.disabled, false);
});
