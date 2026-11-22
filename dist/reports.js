let currentReport;
let reportRequest = 0;

function reportPanel() {
  return `<h2>Báo cáo</h2><form id="frm007_bc_don_dat" class="form" data-validated novalidate onsubmit="submitReport(event)">
    <div class="toolbar">
      <label>Báo cáo<select name="kind">${reportPresenter.options().map(([key,name]) =>
        `<option value="${key}">${name}</option>`).join('')}</select></label>
      <label>Tour<select name="tour"><option value="">Tất cả tour</option>${tours.map(t =>
        `<option value="${esc(t.id)}">${esc(t.title)}</option>`).join('')}</select></label>
      <label>Từ ngày<input type="date" name="from"></label>
      <label>Đến ngày<input type="date" name="to"></label>
      <button type="submit">Áp dụng</button><button type="button" class="outline" onclick="resetReport()">Xóa lọc</button>
    </div>
    <p class="submission-error" role="alert"></p>
  </form><div class="toolbar">
    <button id="report-excel" class="outline" data-report-export onclick="downloadReport('xlsx')" disabled>Tải Excel</button>
    <button class="outline" data-report-export onclick="downloadReport('csv')" disabled>Tải CSV</button>
    <button id="report-pdf" data-report-export class="outline" onclick="window.print()" disabled>In / Lưu PDF</button>
  </div><section id="report-output" aria-live="polite"></section>`;
}

function submitReport(event) {
  event.preventDefault();
  loadReport();
}

function resetReport() {
  const form = $('#frm007_bc_don_dat');
  const kind = form.elements.kind.value;
  form.reset();
  form.elements.kind.value = kind;
  loadReport();
}

async function loadReport() {
  const form = $('#frm007_bc_don_dat');
  if (!form) return;
  const request = ++reportRequest;
  const filter = Object.fromEntries(new FormData(form));
  const { kind, ...params } = filter;
  const output = $('#report-output');
  const exports = document.querySelectorAll('[data-report-export]');
  exports.forEach(button => { button.disabled = true; });
  currentReport = null;
  output.textContent = '';
  form.querySelector('.submission-error').textContent = '';
  const reversed = params.from && params.to && params.from > params.to;
  if (!validateMingoForm(form, reversed ? { to: 'Ngày kết thúc phải từ ngày bắt đầu trở đi.' } : {})) return;
  output.textContent = 'Đang tính báo cáo…';
  try {
    const data = await operationsApi('reports?' + new URLSearchParams(params));
    if (request !== reportRequest || !output.isConnected) return;
    const body = reportPresenter.present(kind, data);
    const printedOn = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date());
    const range = [params.from && 'từ ' + date(params.from), params.to && 'đến ' + date(params.to)].filter(Boolean).join(' ');
    const scope = (tours.find(t => t.id === params.tour)?.title || 'Tất cả tour') + ' · ' + (range || 'Mọi kỳ');
    currentReport = { ...body, kind, scope, printedOn };
    output.innerHTML = reportMarkup(currentReport);
    exports.forEach(button => { button.disabled = false; });
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

function downloadReport(format) {
  const report = currentReport;
  const exporter = reportExporters.get(format);
  if (!report || !exporter) return;
  const blob = exporter.export([[report.title], ['Ngày xuất', report.printedOn], ['Phạm vi', report.scope],
    [report.note], [], report.headers, ...report.rows, report.total]);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'mingo-' + report.kind + '.' + exporter.extension;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
