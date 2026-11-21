import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import { BookingRepository } from '../worker/database/booking-repository.js';
import { ReportsRepository } from '../worker/database/reports-repository.js';
import { AdministratorAccount, CustomerAccount } from '../worker/domain/account.js';
import { AccessPolicy } from '../worker/service/access-policy.js';
import { BookingService } from '../worker/service/booking-service.js';
import { ReportsService } from '../worker/service/reports-service.js';
import { customerId, lastSeatsFixture, tourId } from './fixtures/axis5.js';
import { makeWorker } from './local-worker.js';

test('IT-01 | Giữ đúng ba chỗ cuối và chốt giá cùng lúc tạo đơn', async t => {
  const fixture = await lastSeatsFixture();
  t.after(() => fixture.db.close());

  const response = await fixture.placeBooking();

  assert.equal(response.status, 201, 'Ba khách phải đặt được khi đợt còn đúng ba chỗ');
  const { id } = await response.json();
  const order = fixture.db.prepare('SELECT unit_price,title,adults,children,status FROM bookings WHERE id = ?').get(id);
  assert.deepEqual({ ...order }, {
    unit_price: 500000, title: 'Tour thử trục 5', adults: 2, children: 1, status: 'pending',
  });
  assert.deepEqual({ ...fixture.departure() }, { capacity: 3, reserved: 3 });
  assert.equal((await fixture.placeBooking()).status, 409);
  assert.equal(fixture.db.prepare('SELECT COUNT(*) AS n FROM bookings').get().n, 1);
});

test('IT-02 | Lỗi sau khi ghi đơn, ngay khi tăng chỗ, rollback cả hai bảng', async t => {
  const fixture = await lastSeatsFixture();
  t.after(() => fixture.db.close());
  fixture.db.exec(`
    CREATE TRIGGER axis5_fail_reserve BEFORE UPDATE OF reserved ON departures
    WHEN NEW.tour_id = 'axis5-tour' AND NEW.reserved > OLD.reserved
    BEGIN SELECT RAISE(ABORT, 'axis5:test reserve failure'); END;
  `);

  const failed = await fixture.placeBooking();

  assert.equal(failed.status, 500);
  const body = await failed.json();
  assert.equal(body.error, 'Không thể xử lý yêu cầu lúc này.');
  assert.equal(fixture.db.prepare('SELECT COUNT(*) AS n FROM bookings').get().n, 0);
  assert.deepEqual({ ...fixture.departure() }, { capacity: 3, reserved: 0 });
  fixture.db.exec('DROP TRIGGER axis5_fail_reserve');
  assert.equal((await fixture.placeBooking()).status, 201);
  assert.equal(fixture.departure().reserved, 3);
});

const reportSeed = `
  INSERT INTO accounts (id,username,name,password_hash,salt)
  VALUES ('report-guest','report_guest','Khách thử','fixture-only','fixture-only');
  INSERT INTO tours (id,price,content) VALUES
    ('report-tour',750000,'{"title":"Tour báo cáo"}'),
    ('report-decoy',900000,'{"title":"Tour khác"}');
  INSERT INTO departures (tour_id,day,capacity) VALUES
    ('report-tour','2028-05-09',6),
    ('report-tour','2028-05-10',6),
    ('report-tour','2028-05-12',6),
    ('report-tour','2028-05-13',6),
    ('report-decoy','2028-05-11',6);
  INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price,status,paid) VALUES
    ('lower','report-guest','report-tour','2028-05-10','Tour báo cáo','Khách thử','0900000000',2,0,750000,'confirmed',1),
    ('cancelled','report-guest','report-tour','2028-05-12','Tour báo cáo','Khách thử','0900000000',1,0,1000000,'confirmed',0),
    ('upper','report-guest','report-tour','2028-05-12','Tour báo cáo','Khách thử','0900000000',2,1,750000,'pending',0),
    ('before','report-guest','report-tour','2028-05-09','Tour báo cáo','Khách thử','0900000000',1,0,400000,'confirmed',1),
    ('after','report-guest','report-tour','2028-05-13','Tour báo cáo','Khách thử','0900000000',1,0,600000,'confirmed',1),
    ('decoy','report-guest','report-decoy','2028-05-11','Tour khác','Khách thử','0900000000',1,0,900000,'confirmed',1);
  UPDATE bookings SET status = 'cancelled' WHERE id = 'cancelled';
  INSERT INTO payment_events (booking_id,recorded_on,kind,amount) VALUES
    ('lower','2028-05-10','collect',1500000),
    ('cancelled','2028-05-11','collect',1000000),
    ('cancelled','2028-05-12','refund',1000000),
    ('before','2028-05-09','collect',400000),
    ('after','2028-05-13','collect',600000),
    ('decoy','2028-05-11','collect',900000);
`;

test('IT-03 | Hai biên ngày, lọc đúng tour, đối chiếu từng đồng và loại đơn hủy khỏi tổng', async t => {
  const { db, env } = await makeWorker({ seed: reportSeed });
  t.after(() => db.close());
  const admin = new AccessPolicy(new AdministratorAccount('test_admin'));
  const service = new ReportsService(new ReportsRepository(env.DB), admin, '2028-05-01');
  const filter = new URLSearchParams({ from: '2028-05-10', to: '2028-05-12', tour: 'report-tour' });

  const result = await service.load(filter);

  assert.deepEqual(result.cash.map(row => ({ ...row })), [{ month: '2028-05', collected: 2500000, refunded: 1000000 }]);
  assert.deepEqual(result.capacity.map(row => [row.day, row.reserved, row.available]), [
    ['2028-05-10', 2, 4], ['2028-05-12', 3, 3],
  ]);
  const source = readFileSync(new URL('../dist/report-strategies.js', import.meta.url), 'utf8');
  const { cashTotal, bookingTotal, cancelledLine } = JSON.parse(vm.runInNewContext(source + `
    const bookings = reportPresenter.present('bookings', result);
    JSON.stringify({
      cashTotal: reportPresenter.present('cash', result).total,
      bookingTotal: bookings.total,
      cancelledLine: bookings.rows.find(row => row[1] === 'Đã hủy'),
    })
  `, { result }));
  assert.deepEqual(cashTotal, ['Tổng cộng', 2500000, 1000000, 1500000]);
  assert.deepEqual(bookingTotal, ['Tổng cộng', 'Không gồm đơn hủy', 2, 5]);
  assert.deepEqual(cancelledLine, ['2028-05', 'Đã hủy', 1, 1]);
  const singleDay = await service.load(new URLSearchParams({ from: '2028-05-12', to: '2028-05-12', tour: 'report-tour' }));
  assert.deepEqual(singleDay.cash.map(row => ({ ...row })), [{ month: '2028-05', collected: 0, refunded: 1000000 }]);
});

test('IT-04 | Khách gọi trực tiếp BLL không thể thu tiền, xem báo cáo hoặc hủy đơn của người khác', async t => {
  const fixture = await lastSeatsFixture();
  t.after(() => fixture.db.close());
  const placed = await fixture.placeBooking();
  const { id } = await placed.json();
  assert.equal(placed.status, 201);
  const guest = new AccessPolicy(new CustomerAccount({ id: customerId, name: 'Khách', username: 'axis5_guest' }));
  const stranger = new AccessPolicy(new CustomerAccount({ id: 'other-user', name: 'Khách khác', username: 'other_user' }));
  const repository = new BookingRepository(fixture.env.DB);
  const bookings = new BookingService(repository, guest, fixture.day);
  const reports = new ReportsService(new ReportsRepository(fixture.env.DB), guest, fixture.day);
  const queriesBefore = fixture.queries.length;

  await assert.rejects(bookings.updateBooking(id, 'collect'), { status: 403 });
  await assert.rejects(reports.load(new URLSearchParams()), { status: 403 });
  assert.equal(fixture.queries.length, queriesBefore, 'Hai lệnh bị chặn trước khi chạm DAL');
  await assert.rejects(new BookingService(repository, stranger, fixture.day).updateBooking(id, 'cancel'), { status: 409 });

  const unchanged = fixture.db.prepare('SELECT paid,status FROM bookings WHERE id = ?').get(id);
  assert.deepEqual({ ...unchanged }, { paid: 0, status: 'pending' });
  assert.equal(fixture.departure().reserved, 3);
  assert.equal(fixture.db.prepare('SELECT COUNT(*) AS n FROM payment_events').get().n, 0);
  assert.equal(fixture.db.prepare('SELECT COUNT(*) AS n FROM bookings WHERE tour_id = ?').get(tourId).n, 1);
});
