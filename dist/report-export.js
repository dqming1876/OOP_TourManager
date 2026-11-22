// Minimal XLSX writer for the report's one tab. Text is always stored as text.
function excelXml(value) {
  return String(value).replace(/[\u0000-\u0008\u000B-\u000C\u000E-\u001F]/g, '').replace(/[&<>"]/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
}

function zipStored(files) {
  const encoder = new TextEncoder();
  const contents = [], directory = [];
  let offset = 0;
  function bytes(size, initialize) {
    const data = new Uint8Array(size);
    initialize(new DataView(data.buffer));
    return data;
  }
  for (const [path, source] of Object.entries(files)) {
    const name = encoder.encode(path);
    const data = encoder.encode(source);
    let crc = 0xffffffff;
    for (const value of data) {
      crc ^= value;
      for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
    const checksum = (crc ^ 0xffffffff) >>> 0;
    const local = bytes(30, view => {
      view.setUint32(0, 0x04034b50, true);
      view.setUint16(4, 20, true);
      view.setUint16(12, 0x21, true);
      view.setUint32(14, checksum, true);
      view.setUint32(18, data.length, true);
      view.setUint32(22, data.length, true);
      view.setUint16(26, name.length, true);
    });
    const entry = bytes(46, view => {
      view.setUint32(0, 0x02014b50, true);
      view.setUint16(4, 20, true);
      view.setUint16(6, 20, true);
      view.setUint16(14, 0x21, true);
      view.setUint32(16, checksum, true);
      view.setUint32(20, data.length, true);
      view.setUint32(24, data.length, true);
      view.setUint16(28, name.length, true);
      view.setUint32(42, offset, true);
    });
    contents.push(local, name, data);
    directory.push(entry, name);
    offset += local.length + name.length + data.length;
  }
  const footer = bytes(22, view => {
    const count = Object.keys(files).length;
    view.setUint32(0, 0x06054b50, true);
    view.setUint16(8, count, true);
    view.setUint16(10, count, true);
    view.setUint32(12, directory.reduce((total, item) => total + item.length, 0), true);
    view.setUint32(16, offset, true);
  });
  return new Blob([...contents, ...directory, footer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

function reportWorkbook(rows) {
  const schema = 'http://schemas.openxmlformats.org';
  const office = schema + '/officeDocument/2006/relationships';
  const relationships = `<Relationships xmlns="${schema}/package/2006/relationships">`;
  const sheetRows = rows.map((row, index) => `<row r="${index + 1}">${row.map((value, col) => {
    const position = String.fromCharCode(65 + col) + (index + 1);
    return typeof value === 'number'
      ? `<c r="${position}"><v>${value}</v></c>`
      : `<c r="${position}" t="inlineStr"><is><t xml:space="preserve">${excelXml(value)}</t></is></c>`;
  }).join('')}</row>`).join('');
  return zipStored({
    '[Content_Types].xml': `<Types xmlns="${schema}/package/2006/content-types">
      <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
      <Default Extension="xml" ContentType="application/xml"/>
      <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
      <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
    </Types>`,
    '_rels/.rels': `${relationships}<Relationship Id="rId1" Type="${office}/officeDocument" Target="xl/workbook.xml"/></Relationships>`,
    'xl/workbook.xml': `<workbook xmlns="${schema}/spreadsheetml/2006/main" xmlns:r="${office}">
      <sheets><sheet name="Báo cáo" sheetId="1" r:id="rId1"/></sheets></workbook>`,
    'xl/_rels/workbook.xml.rels': `${relationships}<Relationship Id="rId1" Type="${office}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>`,
    'xl/worksheets/sheet1.xml': `<worksheet xmlns="${schema}/spreadsheetml/2006/main">
      <cols><col min="1" max="1" width="25" customWidth="1"/><col min="2" max="2" width="48" customWidth="1"/>
      <col min="3" max="6" width="20" customWidth="1"/></cols><sheetData>${sheetRows}</sheetData></worksheet>`,
  });
}

class XlsxReportExporter {
  get extension() { return 'xlsx'; }
  export(rows) { return reportWorkbook(rows); }
}

class CsvReportExporter {
  get extension() { return 'csv'; }
  export(rows) {
    const field = value => {
      let text = String(value ?? '');
      // Keep spreadsheet software from treating user-supplied labels as formulas.
      if (typeof value === 'string' && /^[\s]*[=+@-]|^[\t\r\n]/.test(text)) text = "'" + text;
      return '"' + text.replaceAll('"', '""') + '"';
    };
    return new Blob(['\uFEFF', rows.map(row => row.map(field).join(',')).join('\r\n')], {
      type: 'text/csv;charset=utf-8',
    });
  }
}

const reportExporters = new Map([
  ['xlsx', new XlsxReportExporter()],
  ['csv', new CsvReportExporter()],
]);
