import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../../dist/admin.js', import.meta.url), 'utf8');

test('Admin overview reflects shared live orders and only bookable tours', async () => {
  const status = { textContent: '' };
  const content = {
    isConnected: true,
    querySelector: () => null,
    replaceChildren(next) { this.html = next.innerHTML; },
  };
  const tours = [
    { id: 'open', title: 'Tour open', departures: [{ day: '2026-11-22', remaining: 3 }] },
    { id: 'past', title: 'Tour past', departures: [{ day: '2026-11-21', remaining: 3 }] },
    { id: 'full', title: 'Tour full', departures: [{ day: '2026-11-23', remaining: 0 }] },
    { id: 'hidden', title: 'Tour hidden', hidden: true, departures: [{ day: '2026-11-23', remaining: 3 }] },
  ];
  const context = vm.createContext({
    document: {
      hidden: false,
      addEventListener() {},
      createElement() {
        return { set innerHTML(value) { this.content.innerHTML = value; }, content: { querySelector: () => null } };
      },
    },
    location: { hash: '#admin' },
    $: id => ({ '#admin-live-data': content, '#admin-sync-status': status })[id],
    adminTab: 'overview',
    bookings: [],
    tours: [],
    todayInVietnam: () => '2026-11-22',
    date: String, wholeNumber: String, money: String, esc: String,
    bookingStatusLabel: booking => booking.status,
  });
  vm.runInContext(source, context);
  assert.match(vm.runInContext("adminLiveContent('overview')", context), /Chưa có đơn/);

  context.refreshOperations = async ({ includeBookings }) => {
    assert.equal(includeBookings, true);
    context.tours = tours;
    context.bookings = [
      { id: 'ORDER-NEW', title: 'Tour open', date: '2026-11-22', status: 'pending' },
      { id: 'ORDER-PAST', title: 'Tour past', date: '2026-11-21', status: 'pending' },
    ];
    return true;
  };
  await vm.runInContext('syncAdmin()', context);
  assert.match(content.html, /Tour đang bán<\/small><b>1/);
  assert.match(content.html, /Đơn chờ xác nhận<\/small><b>1/);
  assert.match(content.html, /ORDER-NEW/);
  assert.doesNotMatch(content.html, /ORDER-PAST|Tour past|Tour full|Tour hidden/);
  assert.match(status.textContent, /Đã cập nhật/);
});
