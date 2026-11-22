"""Serve the complete Mingo demo on localhost with fresh SQLite data."""

import asyncio
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlsplit

from backend.app import Request, Response
from backend.pricing import pricing_from_percent
from scripts.demo_data import DEMO_PASSWORD, demo_sql
from scripts.sqlite_worker import ROOT, LocalWorker

DIST = ROOT / "dist"
mimetypes.add_type("text/javascript", ".js")


async def assets(request):
    path = unquote(urlsplit(request.url).path)
    filename = (DIST / (path.lstrip("/") or "index.html")).resolve()
    if not filename.is_relative_to(DIST) or filename.is_relative_to(DIST / "server") or not filename.is_file():
        return Response("Not found", 404)
    data = filename.read_bytes()
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return Response(data, headers=[("Content-Type", content_type), ("X-Content-Type-Options", "nosniff")])


def handler_for(worker, port):
    class DemoHandler(BaseHTTPRequestHandler):
        def handle_request(self):
            host = self.headers.get("Host")
            if host not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                self.send_error(400, "Use localhost")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400)
                return
            if length < 0:
                self.send_error(400)
                return
            if length > 12_000_000:
                self.send_error(413)
                return
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            request = Request(self.command, f"http://{host}{self.path}", dict(self.headers), body)
            reply = asyncio.run(worker.fetch(request))
            data = reply.body if isinstance(reply.body, bytes) else reply.body.encode("utf-8")
            self.send_response(reply.status)
            for name, value in reply.headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if request.method != "HEAD":
                self.wfile.write(data)

        do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = handle_request

    return DemoHandler


def main():
    port = int(os.environ.get("MINGO_DEMO_PORT", "4173"))
    pricing = pricing_from_percent(os.environ.get("MINGO_DISCOUNT_PERCENT"))
    worker = LocalWorker(
        admin_password=os.environ.get("MINGO_DEMO_PASSWORD"),
        seed=demo_sql(),
        assets=assets,
        pricing=pricing,
    )
    try:
        with HTTPServer(("127.0.0.1", port), handler_for(worker, port)) as server:
            print(f"Mingo demo: http://127.0.0.1:{port}", flush=True)
            print(f"Admin demo_admin — mật khẩu phiên này: {worker.admin_password}", flush=True)
            print(f"Khách mingo_khach1 — mật khẩu mẫu: {DEMO_PASSWORD}", flush=True)
            if getattr(pricing, "percent", 0):
                print(f"Chính sách giá: giảm {pricing.percent}% (PercentageDiscount)", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        worker.database.close()


if __name__ == "__main__":
    main()
