import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

test('4.6: Thêm Concrete Strategy mà không sửa Presenter hoặc ba biến thể cũ', () => {
  const context = vm.createContext({ date: day => day.split('-').reverse().join('/') });
  const source = readFileSync(new URL('../../dist/report-strategies.js', import.meta.url), 'utf8');
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

test('IT-03: Tổng trình bày và dòng đơn hủy', () => {
  const result = {
    cash: [{ month: '2028-05', collected: 2500000, refunded: 1000000 }],
    bookings: [{ month: '2028-05', state: 'cancelled', orders: 1, guests: 1 },
      { month: '2028-05', state: 'confirmed', orders: 1, guests: 2 },
      { month: '2028-05', state: 'pending', orders: 1, guests: 3 }],
  };
  const source = readFileSync(new URL('../../dist/report-strategies.js', import.meta.url), 'utf8');
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
});
