"""Opt-in browser/export checks; needs playwright, openpyxl and pymupdf plus Chromium.
Run: python3 -m tests.ui_review. Starts only a disposable localhost SQLite demo.
"""
import os
import subprocess
import sys
import time
from pathlib import Path
from secrets import token_hex
from urllib.request import urlopen


def main():
    from playwright.sync_api import sync_playwright
    import openpyxl
    import fitz
    root = Path(__file__).resolve().parents[1]
    output = root / 'docs/evidence'
    output.mkdir(exist_ok=True)
    password = token_hex(24)
    base = 'http://127.0.0.1:4179'
    process = subprocess.Popen([sys.executable, '-m', 'scripts.demo'], cwd=root,
        env={**os.environ, 'MINGO_DEMO_PORT': '4179', 'MINGO_DEMO_PASSWORD': password},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                if urlopen(base, timeout=1).status == 200:
                    break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Demo did not start')
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),
                                        headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            login = context.request.post(base+'/api/auth/login',
                data={'username':'demo_admin','password':password},headers={'Origin':base})
            assert login.ok, login.status
            page = context.new_page()
            errors=[]
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base+'/#admin')
            page.wait_for_function("typeof showAdminTab === 'function'")
            page.evaluate("showAdminTab('reports')")
            page.wait_for_selector('#report-output tfoot')
            assert 'Ngày xuất' in page.locator('#report-output').inner_text()
            with page.expect_download() as download:
                page.locator('#report-excel').click()
            xlsx = output/'review-report.xlsx'
            download.value.save_as(xlsx)
            workbook=openpyxl.load_workbook(xlsx, data_only=True)
            rows=list(workbook.active.values)
            assert rows[0][0] and rows[1][0]=='Ngày xuất'
            assert rows[-1][0]=='Tổng cộng'
            pdf=output/'review-report.pdf'
            page.pdf(path=str(pdf), format='A4', print_background=True)
            doc=fitz.open(pdf)
            text='\n'.join(page.get_text() for page in doc)
            assert 'Ngày xuất' in text and 'Tổng cộng' in text, text
            assert '\ufffd' not in text
            doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(output/'review-report.png')
            # UI edit and a separate browser session read the same database value.
            page.evaluate("showAdminTab('destinations')")
            page.wait_for_function('typeof destinationEntries !== "undefined" && destinationEntries.length === 204')
            page.locator('#edit-province').select_option('1')
            page.locator('#destination-editor button').first.click()
            page.locator('#frm009_dm_diem_den [name=description]').fill('Minh chứng đồng bộ địa danh giữa hai phiên.')
            page.locator('#frm009_dm_diem_den [name=url]').fill('https://example.com/demo.jpg')
            page.locator('#frm009_dm_diem_den [name=source]').fill('Nguồn minh họa kiểm thử')
            page.locator('#frm009_dm_diem_den button').click()
            page.wait_for_function("!document.querySelector('#modal').open")
            other=browser.new_context()
            result=other.request.get(base+'/api/ops/destinations').json()
            assert result['entries'][0]['description']=='Minh chứng đồng bộ địa danh giữa hai phiên.'
            assert not errors, errors
            browser.close()
            print(f'PASS: browser admin, shared destination edit/read, XLSX ({len(rows)} rows), PDF ({len(doc)} pages), Vietnamese text/title/date/total.')
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__=='__main__':
    main()
