"""HTTP boundary, shared by Cloudflare and the Python demo server."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit
from uuid import uuid4

from .auth import ADMIN_COOKIE, CUSTOMER_COOKIE, clear_cookie, create_session, derive_password, session_identity
from .domain import ADMIN, CUSTOMER, AccessError, AppError, ValidationError, text_length
from .destinations import DestinationsService
from .repositories import DestinationsRepository, AccountsRepository, BookingRepository, ReportsRepository, TourCatalogRepository
from .services import AccessPolicy, AccountsService, BookingService, ReportsService, TourCatalogService

LOGGER = logging.getLogger(__name__)
VIETNAM = timezone(timedelta(hours=7))
NOT_FOUND = "Không tìm thấy chức năng."
JSON_HEADERS = [("Content-Type", "application/json"), ("Cache-Control", "no-store")]


@dataclass
class Request:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    def header(self, name):
        key = name.lower()
        return next((value for header, value in self.headers.items() if header.lower() == key), None)

    async def text(self, limit):
        return self.body


@dataclass
class Response:
    body: bytes | str = ""
    status: int = 200
    headers: list[tuple[str, str]] = field(default_factory=list)


def json_response(data, status=200, cookies=()):
    return Response(
        json.dumps(data, ensure_ascii=True, separators=(",", ":")), status,
        [*JSON_HEADERS, *(("Set-Cookie", cookie) for cookie in cookies)],
    )


def require_post(request):
    if request.method != "POST":
        raise AppError(405, "Phương thức không hợp lệ.")
    url = urlsplit(request.url)
    if request.header("Origin") != f"{url.scheme}://{url.netloc}":
        raise AccessError(403, "Nguồn yêu cầu không hợp lệ.")


def reject_constant(_value):
    raise ValueError("Non-JSON constant")


async def read_object(request, limit):
    raw = await request.text(limit)
    if text_length(raw) > limit:
        raise AppError(413, "Dữ liệu quá lớn.")
    try:
        body = json.loads(raw, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        body = None
    if not isinstance(body, dict):
        raise ValidationError("Dữ liệu không hợp lệ.")
    return body


def request_identity(request, settings):
    return (session_identity(request, settings.secret, ADMIN_COOKIE)
            or session_identity(request, settings.secret, CUSTOMER_COOKIE))


async def accounts_route(request, path, accounts, settings):
    if request.method == "GET":
        if path == "/api/auth/me":
            user = await accounts.current_account(request_identity(request, settings))
            return json_response({"user": user.public() if user else None})
        if path == "/api/admin/session":
            actor = await accounts.current_account(request_identity(request, settings))
            return json_response({"authenticated": bool(actor and actor.manages_catalog)})
    login = path in ("/api/auth/login", "/api/admin/login")
    logout = path in ("/api/auth/logout", "/api/admin/logout")
    if not (login or logout or path in ("/api/profile", "/api/auth/register")):
        raise AppError(404, NOT_FOUND)
    require_post(request)
    if logout:
        cookies = [clear_cookie(ADMIN_COOKIE)]
        if path == "/api/auth/logout":
            cookies.append(clear_cookie(CUSTOMER_COOKIE))
        return json_response({"ok": True}, cookies=cookies)
    body = await read_object(request, 8192)
    if path == "/api/profile":
        return json_response({"user": await accounts.save_customer_profile(request_identity(request, settings), body)})
    if path == "/api/auth/register":
        await accounts.register_account(request.header("CF-Connecting-IP") or "local", body)
        return json_response({"ok": True}, 201)
    legacy = path == "/api/admin/login"
    user = await accounts.login_account(request.header("CF-Connecting-IP") or "local", body, legacy)
    cookie = ADMIN_COOKIE if user["role"] == ADMIN else CUSTOMER_COOKIE
    token = create_session(cookie, settings.secret, user["id"] if user["role"] == CUSTOMER else None)
    return json_response({"ok": True} if legacy else {"user": user}, cookies=(
        clear_cookie(CUSTOMER_COOKIE if cookie == ADMIN_COOKIE else ADMIN_COOKIE), token,
    ))


async def operations_route(request, url, catalog, bookings, reports, access, destinations):
    parts = url.path.split("/")[3:]
    if len(parts) > 3:
        raise AppError(404, NOT_FOUND)
    resource, item_id, action = (parts + [""] * 3)[:3]
    if request.method == "GET" and not item_id:
        if resource == "destinations":
            return json_response({"entries": await destinations.entries()})
        if resource == "tours":
            return json_response({"tours": await catalog.catalog()})
        if resource == "bookings":
            return json_response({"bookings": await bookings.bookings()})
        if resource == "reports":
            params = {}
            for key, value in parse_qsl(url.query, keep_blank_values=True):
                params.setdefault(key, value)
            return json_response(await reports.load(params))
        raise AppError(404, NOT_FOUND)
    if request.method == "GET" and resource == "bookings" and item_id and action == "payments":
        return json_response({"payments": await bookings.payment_history(item_id)})
    require_post(request)
    customer_action = resource == "bookings" and (
        not item_id or (action == "cancel" and access.actor and access.actor.cancellation_owner() is not None)
    )
    access.require_role(CUSTOMER if customer_action else ADMIN)
    body = await read_object(request, 3_000_000)
    if resource == "destinations":
        if action == "remove" and item_id:
            await destinations.remove(item_id, body)
        elif not action:
            await destinations.save(item_id, body)
        else:
            raise AppError(404, NOT_FOUND)
        return json_response({"ok": True})
    if resource == "tours" and not action:
        return json_response(await catalog.save_tour(item_id, body), 200 if item_id else 201)
    if resource == "tours" and item_id and action == "visibility":
        await catalog.set_visibility(item_id, body.get("hidden"))
    elif resource == "tours" and item_id and action == "departures":
        await catalog.save_departure(item_id, body)
    elif resource == "tours" and item_id and action == "remove-departure":
        await catalog.remove_departure(item_id, body.get("day"))
    elif resource == "bookings" and not item_id:
        return json_response(await bookings.place_booking(body), 201)
    elif resource == "bookings" and action:
        await bookings.update_booking(item_id, action)
    else:
        raise AppError(404, NOT_FOUND)
    return json_response({"ok": True})


def local_day():
    return datetime.now(VIETNAM).date().isoformat()


@dataclass(frozen=True)
class Repositories:
    accounts: type = AccountsRepository
    bookings: type = BookingRepository
    catalog: type = TourCatalogRepository
    reports: type = ReportsRepository
    destinations: type = DestinationsRepository


class Application:
    def __init__(self, repositories=None, today=local_day, derive=derive_password):
        self.repositories = repositories or Repositories()
        self.today = today
        self.derive = derive

    async def fetch(self, request, db, settings, assets):
        url = urlsplit(request.url)
        try:
            if url.path.startswith("/api/"):
                repo = self.repositories
                accounts = AccountsService(repo.accounts(db) if db is not None else None, settings, self.derive)
                if not url.path.startswith("/api/ops/"):
                    return await accounts_route(request, url.path, accounts, settings)
                access = AccessPolicy(await accounts.current_account(request_identity(request, settings)))
                day = self.today()
                return await operations_route(
                    request, url, TourCatalogService(repo.catalog(db), access, day),
                    BookingService(repo.bookings(db), access, day), ReportsService(repo.reports(db), access, day), access,
                    DestinationsService(repo.destinations(db), access),
                )
            if url.path == "/admin.js":
                accounts = AccountsService(self.repositories.accounts(db), settings, self.derive)
                actor = await accounts.current_account(request_identity(request, settings))
                if not actor or not actor.manages_catalog:
                    return Response("Unauthorized", 401, [("Cache-Control", "no-store")])
            if request.method not in ("GET", "HEAD"):
                return Response("Method not allowed", 405)
            return await assets(request)
        except AppError as error:
            data = {"error": str(error)}
            if error.field is not None:
                data["field"] = error.field
            return json_response(data, error.status)
        except Exception as error:
            request_id = str(uuid4())
            LOGGER.error("Unexpected Worker error %s %s", request_id, type(error).__name__)
            return json_response({"error": "Không thể xử lý yêu cầu lúc này.", "requestId": request_id}, 500)
