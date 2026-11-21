import assert from 'node:assert/strict';
import test, { mock } from 'node:test';
import { AdministratorAccount, CustomerAccount } from '../worker/domain/account.js';
import { Booking } from '../worker/domain/booking.js';
import { Departure } from '../worker/domain/departure.js';
import { PaymentEvent } from '../worker/domain/payment-event.js';
import { Tour } from '../worker/domain/tour.js';
import { AccessPolicy } from '../worker/service/access-policy.js';
import { BookingService } from '../worker/service/booking-service.js';
import { ReportsService } from '../worker/service/reports-service.js';
import { TourCatalogService } from '../worker/service/tour-catalog-service.js';

const today = '2028-02-29';
const fakeClock = () => today;
const customer = new AccessPolicy(new CustomerAccount({ id: 'customer-1', name: 'Linh', username: 'linh' }));
const admin = new AccessPolicy(new AdministratorAccount('test_admin'));
const request = Object.freeze({
  tourId: 'tour-1', day: today, name: 'Khách mẫu', phone: '0900000000', adults: 1, children: 0,
});

test('UT-01 | BVA — số người lớn nhận 1 và 100, từ chối 0 và 101', () => {
  // Arrange
  const make = adults => Booking.request('order-1', 'customer-1', { ...request, adults });
  // Act + Assert
  assert.equal(make(1).people, 1);
  assert.equal(make(100).people, 100);
  assert.throws(() => make(0), { status: 400, field: 'adults' });
  assert.throws(() => make(101), { status: 400, field: 'adults' });
});

test('UT-02 | BVA — số trẻ em nhận 0 và 99, từ chối -1 và 100', () => {
  const make = children => Booking.request('order-1', 'customer-1', { ...request, children });
  assert.equal(make(0).people, 1);
  assert.equal(make(99).people, 100);
  assert.throws(() => make(-1), { status: 400, field: 'children' });
  assert.throws(() => make(100), { status: 400, field: 'children' });
});

test('UT-03 | EP — điện thoại có dấu phân nhóm hợp lệ, chữ và số quá ngắn bị từ chối', () => {
  const make = phone => Booking.request('order-1', 'customer-1', { ...request, phone });
  const local = make(' 090-123-4567 ');
  assert.equal(local.phone, '090-123-4567');
  assert.throws(() => make('090123456X'), { status: 400, field: 'phone' });
  assert.throws(() => make('1234567--'), { status: 400, field: 'phone' });
});

test('UT-04 | EP — 3 khách trả 1.500.000 theo giá chốt; bản nháp chưa có tổng tiền', () => {
  const saved = new Booking({ adults: 2, children: 1, unitPrice: 500000 });
  const draft = Booking.request('draft-1', 'customer-1', request);
  const amount = saved.total;
  assert.equal(amount, 1500000);
  assert.throws(() => draft.total, { status: 409 });
});

test('UT-05 | BVA — sức chứa tối thiểu 1, tối đa 100', () => {
  const make = capacity => new Departure('tour-1', today, capacity);
  assert.equal(make(1).remaining, 1);
  assert.equal(make(100).remaining, 100);
  assert.throws(() => make(0), { status: 400, field: 'capacity' });
  assert.throws(() => make(101), { status: 400, field: 'capacity' });
});

test('UT-06 | BVA — lịch ngày nhuận, đúng ngày được lưu, ngày trước bị chặn', async () => {
  const createDeparture = mock.fn(async () => true);
  const service = new TourCatalogService({ createDeparture }, admin, fakeClock());
  await assert.rejects(service.saveDeparture('tour-1', { day: '2028-02-28', capacity: 5 }), { status: 400, field: 'day' });
  await assert.rejects(service.saveDeparture('tour-1', { day: '2028-02-30', capacity: 5 }), { status: 400, field: 'day' });
  await service.saveDeparture('tour-1', { day: today, capacity: 5 });
  assert.equal(createDeparture.mock.callCount(), 1);
  const [departure] = createDeparture.mock.calls[0].arguments;
  assert.deepEqual([departure.day, departure.remaining], ['2028-02-29', 5]);
});

test('UT-07 | Ngoại lệ — khách gọi ghi phiếu thu bị chặn trước repository', async () => {
  const updateBooking = mock.fn(async () => true);
  const service = new BookingService({ updateBooking }, customer, fakeClock());
  await assert.rejects(service.updateBooking('order-1', 'collect'), { status: 403 });
  assert.equal(updateBooking.mock.callCount(), 0);
});

test('UT-08 | Ngoại lệ — stub DAL từ chối giữ chỗ, service trả 409 với trường ngày', async () => {
  const placeBooking = mock.fn(async () => false);
  const service = new BookingService({ placeBooking }, customer, fakeClock());
  await assert.rejects(service.placeBooking({ ...request, adults: 2, children: 1 }), { status: 409, field: 'day' });
  assert.equal(placeBooking.mock.callCount(), 1);
  const [booking, cutoff] = placeBooking.mock.calls[0].arguments;
  assert.deepEqual([booking.userId, booking.people, cutoff], ['customer-1', 3, '2028-02-29']);
});

test('UT-09 | State/RBAC — hủy của khách chỉ áp dụng cho đơn chờ đúng chủ', async () => {
  const updateBooking = mock.fn(async () => true);
  const service = new BookingService({ updateBooking }, customer, fakeClock());
  await service.updateBooking('order-1', 'cancel');
  const [id, rule, owner, cutoff] = updateBooking.mock.calls[0].arguments;
  assert.deepEqual(
    [id, rule.from, rule.alsoFrom, rule.to, rule.paid, owner, cutoff],
    ['order-1', 'pending', 'pending', 'cancelled', false, 'customer-1', '2028-02-29'],
  );
});

test('UT-10 | State — thu chỉ từ xác nhận chưa thu, hoàn chỉ từ xác nhận đã thu', async () => {
  const updateBooking = mock.fn(async () => true);
  const service = new BookingService({ updateBooking }, admin, fakeClock());
  await service.updateBooking('order-1', 'collect');
  await service.updateBooking('order-1', 'refund');
  const changes = updateBooking.mock.calls.map(call => {
    const [, rule, owner] = call.arguments;
    return [rule.from, rule.to, rule.paid, rule.nextPaid, owner];
  });
  assert.deepEqual(changes, [
    ['confirmed', 'confirmed', false, true, null],
    ['confirmed', 'confirmed', true, false, null],
  ]);
});

test('UT-11 | BVA — báo cáo nhận khoảng một ngày và loại khoảng đảo', async () => {
  const load = mock.fn(async () => ({ cash: [] }));
  const service = new ReportsService({ load }, admin, fakeClock());
  await assert.rejects(service.load(new URLSearchParams({ from: '2028-03-01', to: today })), { status: 400 });
  await service.load(new URLSearchParams({ from: today, to: today, tour: 'tour-1' }));
  assert.equal(load.mock.callCount(), 1);
  assert.deepEqual(load.mock.calls[0].arguments, [{
    from: '2028-02-29', to: '2028-02-29', tourId: 'tour-1', today: '2028-02-29',
  }]);
});

test('UT-12 | EP — tour 2 ngày có đúng thứ tự điểm ghé, lịch thiếu ngày bị từ chối', () => {
  const input = {
    title: 'Hà Nội', province: 'Hà Nội', place: 'Hồ Gươm', price: 1200000,
    desc: 'Đi bộ và xem bảo tàng', days: 2,
  };
  const tour = new Tour('tour-1', {
    ...input, itinerary: ['Đi bộ', 'Tham quan'], stops: ['Hồ Gươm', 'Bảo tàng Hà Nội'],
  });
  const rows = tour.stops.map(stop => stop.toWriteRow());
  assert.deepEqual(rows, [
    { dayNumber: 1, place: 'Hồ Gươm', activity: 'Đi bộ' },
    { dayNumber: 2, place: 'Bảo tàng Hà Nội', activity: 'Tham quan' },
  ]);
  assert.throws(() => new Tour('tour-1', { ...input, itinerary: ['Đi bộ'] }), { status: 400 });
});

test('UT-13 | EP — thu có dấu dương và hoàn có dấu âm; số tiền 0 không sinh bút toán', () => {
  const collect = new PaymentEvent({ date: today, amount: 1000000, kind: 'collect' });
  const refund = new PaymentEvent({ date: today, amount: 400000, kind: 'refund' });
  const signed = [collect.signedAmount, refund.signedAmount];
  assert.deepEqual(signed, [1000000, -400000]);
  assert.throws(() => new PaymentEvent({ date: today, amount: 0, kind: 'refund' }), { status: 400, field: 'amount' });
});
