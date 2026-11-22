import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../../dist/report-export.js', import.meta.url), 'utf8');
const exporters = vm.runInNewContext(source + '\nreportExporters;', { Blob, TextEncoder });
const rows = [
  ['Doanh thu & chi phí'],
  ['Hà Nội, "Phố cổ"', 1_200_000],
  ['=1+2', -1],
];

function storedZipEntries(buffer) {
  const view = new DataView(buffer);
  const bytes = new Uint8Array(buffer);
  const decoder = new TextDecoder();
  const entries = new Map();
  let offset = 0;

  while (view.getUint32(offset, true) === 0x04034b50) {
    assert.equal(view.getUint16(offset + 8, true), 0, 'XLSX uses stored ZIP entries');
    const size = view.getUint32(offset + 18, true);
    const nameStart = offset + 30;
    const nameEnd = nameStart + view.getUint16(offset + 26, true);
    const start = nameEnd + view.getUint16(offset + 28, true);
    entries.set(decoder.decode(bytes.subarray(nameStart, nameEnd)), decoder.decode(bytes.subarray(start, start + size)));
    offset = start + size;
  }
  assert.equal(view.getUint32(offset, true), 0x02014b50);
  return entries;
}

test('XLSX exporter writes text cells and numeric values to a worksheet', async () => {
  const exporter = exporters.get('xlsx');
  const blob = exporter.export(rows);
  assert.equal(exporter.extension, 'xlsx');
  assert.equal(blob.type, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');

  const entries = storedZipEntries(await blob.arrayBuffer());
  assert.ok(entries.get('xl/workbook.xml').includes('name="Báo cáo"'));
  const sheet = entries.get('xl/worksheets/sheet1.xml');
  assert.ok(sheet.includes('Doanh thu &amp; chi phí'));
  assert.ok(sheet.includes('Hà Nội, &quot;Phố cổ&quot;'));
  assert.match(sheet, /<c r="B2"><v>1200000<\/v><\/c>/);
  assert.match(sheet, /<c r="A3" t="inlineStr"><is><t xml:space="preserve">=1\+2<\/t><\/is><\/c>/);
});

test('CSV exporter writes UTF-8 BOM, escaped text and numerical values', async () => {
  const exporter = exporters.get('csv');
  const blob = exporter.export(rows);
  assert.equal(exporter.extension, 'csv');
  assert.equal(blob.type, 'text/csv;charset=utf-8');
  const bytes = new Uint8Array(await blob.arrayBuffer());
  assert.deepEqual([...bytes.subarray(0, 3)], [0xef, 0xbb, 0xbf]);
  assert.equal(await blob.text(), '"Doanh thu & chi phí"\r\n"Hà Nội, ""Phố cổ""","1200000"\r\n"\'=1+2","-1"');
});
