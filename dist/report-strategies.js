// Strategy: each report owns the shape and calculations of its own result.
function sumReportRows(items, key) {
  return items.reduce((total, row) => total + row[key], 0);
}

class CashReport {
  get title() { return 'Thu, hoàn và doanh thu ròng'; }

  summarize({ cash }) {
    const collected = sumReportRows(cash, 'collected');
    const refunded = sumReportRows(cash, 'refunded');
    return {
      headers: ['Tháng', 'Thu (VND)', 'Hoàn (VND)', 'Thu ròng (VND)'],
      rows: cash.map(row => [row.month, row.collected, row.refunded, row.collected - row.refunded]),
      total: ['Tổng cộng', collected, refunded, collected - refunded],
      chart: cash,
      note: 'Kỳ lọc tính theo ngày ghi nhận tiền. Thu ròng bằng tổng thu trừ tổng hoàn.',
    };
  }
}

const reportState = {
  pending: 'Chờ xác nhận', confirmed: 'Đã xác nhận', cancelled: 'Đã hủy',
  expired: 'Quá hạn xác nhận', completed: 'Đã hoàn thành',
};

class BookingReport {
  get title() { return 'Tình hình đặt tour'; }

  summarize({ bookings }) {
    return {
      headers: ['Tháng khởi hành', 'Trạng thái', 'Số đơn', 'Số khách'],
      rows: bookings.map(row => [row.month, reportState[row.state], row.orders, row.guests]),
      total: ['Tổng cộng', 'Mọi trạng thái', sumReportRows(bookings, 'orders'), sumReportRows(bookings, 'guests')],
      note: 'Số liệu gồm cả đơn hủy và quá hạn. Kỳ lọc tính theo ngày khởi hành.',
    };
  }
}

class CapacityReport {
  get title() { return 'Sức chứa và tỷ lệ lấp đầy'; }

  summarize({ capacity: departures }) {
    const capacity = sumReportRows(departures, 'capacity');
    const reserved = sumReportRows(departures, 'reserved');
    const rate = (used, max) => (max ? (100 * used / max).toFixed(1) : '0.0').replace('.', ',') + '%';
    return {
      headers: ['Ngày khởi hành', 'Tour', 'Sức chứa', 'Đã giữ', 'Còn trống', 'Tỷ lệ'],
      rows: departures.map(row => [
        date(row.day), row.tour, row.capacity, row.reserved, row.available, rate(row.reserved, row.capacity),
      ]),
      total: ['Tổng cộng', '', capacity, reserved, capacity - reserved, rate(reserved, capacity)],
      note: 'Tỷ lệ tổng dùng tổng chỗ giữ chia tổng sức chứa. Đơn đã hủy không giữ chỗ.',
    };
  }
}

class ReportPresenter {
  #strategies;

  constructor(strategies) {
    this.#strategies = new Map(Object.entries(strategies));
  }

  options() {
    return Array.from(this.#strategies, ([kind, strategy]) => [kind, strategy.title]);
  }

  present(kind, data) {
    const strategy = this.#strategies.get(kind);
    if (!strategy) throw new RangeError('Loại báo cáo không hợp lệ.');
    return { title: strategy.title, ...strategy.summarize(data) };
  }
}

const reportPresenter = new ReportPresenter({
  cash: new CashReport(), bookings: new BookingReport(), capacity: new CapacityReport(),
});
