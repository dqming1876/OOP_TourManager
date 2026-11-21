const reportTypes = {
  cash: 'Thu, hoàn và doanh thu ròng',
  bookings: 'Tình hình đặt tour',
  capacity: 'Sức chứa và tỷ lệ lấp đầy',
};
const reportState = {
  pending: 'Chờ xác nhận', confirmed: 'Đã xác nhận', cancelled: 'Đã hủy',
  expired: 'Quá hạn xác nhận', completed: 'Đã hoàn thành',
};
let currentReport;
let reportRequest = 0;

function reportPanel() {
  return `<h2>Báo cáo</h2><form id="report-filters" class="form" onsubmit="submitReport(event)">
    <div class="toolbar">
      <label>Báo cáo<select name="kind">${Object.entries(reportTypes).map(([key,name]) =>
        `<option value="${key}">${name}</option>`).join('')}</select></label>
      <label>Tour<select name="tour"><option value="">Tất cả tour</option>${tours.map(t =>
        `<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('')}</select></label>
      <label>Từ ngày<input type="date" name="from"></label>
      <label>Đến ngày<input type="date" name="to"></label>
      <button type="submit">Áp dụng</button><button type="button" class="outline" onclick="resetReport()">Xóa lọc</button>
    </div>
  </form><div class="toolbar">
    <button id="report-excel" class="outline" onclick="downloadReport()" disabled>Tải Excel</button>
    <button id="report-pdf" class="outline" onclick="window.print()" disabled>In / Lưu PDF</button>
  </div><section id="report-output" aria-live="polite"></section>`;
}

function submitReport(event) {
  event.preventDefault();
  loadReport();
}

function resetReport() {
  const form = $('#report-filters');
  const kind = form.elements.kind.value;
  form.reset();
  form.elements.kind.value = kind;
  loadReport();
}

function reportRows(kind, data) {
  const sum = (items, key) => items.reduce((total, row) => total + row[key], 0);
  if (kind === 'cash') {
    const group = data.cash;
    const collected = sum(group, 'collected'), refunded = sum(group, 'refunded');
    return {
      headers: ['Tháng', 'Thu (VND)', 'Hoàn (VND)', 'Thu ròng (VND)'],
      rows: group.map(r => [r.month, r.collected, r.refunded, r.collected - r.refunded]),
      total: ['Tổng cộng', collected, refunded, collected - refunded],
      chart: group,
      note: 'Kỳ lọc tính theo ngày ghi nhận tiền. Thu ròng bằng tổng thu trừ tổng hoàn.',
    };
  }
  if (kind === 'bookings') {
    const group = data.bookings;
    return {
      headers: ['Tháng khởi hành', 'Trạng thái', 'Số đơn', 'Số khách'],
      rows: group.map(r => [r.month, reportState[r.state], r.orders, r.guests]),
      total: ['Tổng cộng', 'Mọi trạng thái', sum(group, 'orders'), sum(group, 'guests')],
      note: 'Số liệu gồm cả đơn hủy và quá hạn. Kỳ lọc tính theo ngày khởi hành.',
    };
  }
  const group = data.capacity;
  const capacity = sum(group, 'capacity'), reserved = sum(group, 'reserved');
  const rate = (used, max) => (max ? (100 * used / max).toFixed(1) : '0.0').replace('.', ',') + '%';
  return {
    headers: ['Ngày khởi hành', 'Tour', 'Sức chứa', 'Đã giữ', 'Còn trống', 'Tỷ lệ'],
    rows: group.map(r => [date(r.day), r.tour, r.capacity, r.reserved, r.available, rate(r.reserved, r.capacity)]),
    total: ['Tổng cộng', '', capacity, reserved, capacity - reserved, rate(reserved, capacity)],
    note: 'Tỷ lệ tổng dùng tổng chỗ giữ chia tổng sức chứa. Đơn đã hủy không giữ chỗ.',
  };
}

async function loadReport() {
  const form = $('#report-filters');
  if (!form) return;
  const request = ++reportRequest;
  const filter = Object.fromEntries(new FormData(form));
  const { kind, ...params } = filter;
  const output = $('#report-output');
  const excel = $('#report-excel'), pdf = $('#report-pdf');
  excel.disabled = pdf.disabled = true;
  currentReport = null;
  output.textContent = 'Đang tính báo cáo…';
  try {
    const data = await operationsApi('reports?' + new URLSearchParams(params));
    if (request !== reportRequest || !output.isConnected) return;
    const body = reportRows(kind, data);
    const printedOn = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date());
    const range = [params.from && 'từ ' + date(params.from), params.to && 'đến ' + date(params.to)].filter(Boolean).join(' ');
    const scope = (tours.find(t => t.id === params.tour)?.title || 'Tất cả tour') + ' · ' + (range || 'Mọi kỳ');
    currentReport = { kind, title: reportTypes[kind], scope, printedOn, ...body };
    output.innerHTML = reportMarkup(currentReport);
    excel.disabled = pdf.disabled = false;
  } catch (error) {
    if (request === reportRequest && output.isConnected) output.textContent = error.message;
  }
}

function reportMarkup(report) {
  const rows = (values, tag) => `<tr>${values.map(value =>
    `<${tag} ${typeof value === 'number' ? 'class="report-number"' : ''}>${typeof value === 'number'
      ? value.toLocaleString('vi-VN') : esc(value)}</${tag}>`).join('')}</tr>`;
  return `<h3>${esc(report.title)}</h3><p>${esc(report.scope)} · Ngày xuất ${report.printedOn}</p>
    <p class="muted">${esc(report.note)}</p>${cashChart(report.chart)}
    <div class="table-scroll"><table><thead>${rows(report.headers, 'th')}</thead>
    <tbody>${report.rows.length ? report.rows.map(row => rows(row, 'td')).join('') :
      `<tr><td colspan="${report.headers.length}">Không có dữ liệu theo bộ lọc.</td></tr>`}</tbody>
    <tfoot>${rows(report.total, 'td')}</tfoot></table></div>`;
}

function cashChart(group) {
  if (!group?.length) return '';
  const peak = Math.max(1, ...group.flatMap(row => [row.collected, row.refunded]));
  return `<figure class="report-chart"><figcaption>Thu và hoàn theo tháng</figcaption>
    <p><span class="chart-key">Thu</span> <span class="chart-key refunded">Hoàn</span></p>
    ${group.map(row => `<div class="chart-month"><strong>${esc(row.month)}</strong>
    <div><div class="chart-bar" style="width:${row.collected * 100 / peak}%"></div>
    <small>${money(row.collected)}</small>
    <div class="chart-bar refunded" style="width:${row.refunded * 100 / peak}%"></div>
    <small>${money(row.refunded)}</small></div></div>`).join('')}</figure>`;
}

function downloadReport() {
  const report = currentReport;
  if (!report) return;
  const blob = reportWorkbook([[report.title], ['Ngày xuất', report.printedOn], ['Phạm vi', report.scope],
    [report.note], [], report.headers, ...report.rows, report.total]);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'mingo-' + report.kind + '.xlsx';
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
