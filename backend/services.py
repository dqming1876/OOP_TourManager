"""Business services depend on ports, independent of HTTP and D1."""

import re
from dataclasses import replace
from hashlib import sha256
from uuid import uuid4

from .auth import Settings, derive_password, equal
from .login_limits import LoginRateLimiter
from .domain import (
    ADMIN, CUSTOMER, AccessError, AdministratorAccount, AppError, Booking, ConflictError,
    CustomerAccount, Departure, Tour, ValidationError, calendar_day, text_length, integer_between, required_text,
)
from .ports import AccountsPort, BookingPort, ReportsPort, TourCatalogPort


def credentials(body):
    username = body.get("username")
    username = username.strip().lower() if isinstance(username, str) else ""
    password = body.get("password")
    if not username or not isinstance(password, str) or text_length(password) > 128:
        raise ValidationError("Vui lòng nhập tài khoản và mật khẩu.")
    return username, password


class AccountsService:
    def __init__(self, repository: AccountsPort | None, settings: Settings, derive=derive_password):
        self.repository = repository
        self.settings = settings
        self.derive = derive

    def accounts(self):
        if self.repository is None:
            raise AppError(503, "Hệ thống tài khoản chưa sẵn sàng.")
        return self.repository

    async def bootstrap_admin(self):
        settings = self.settings
        if settings.username and settings.salt and settings.password_hash:
            await self.accounts().ensure_admin(settings.username.lower(), settings.password_hash, settings.salt)

    async def current_account(self, identity):
        if not identity:
            return None
        if identity == "admin":
            await self.bootstrap_admin()
        row = await self.accounts().find_public(identity)
        if not row:
            return None
        return AdministratorAccount(row["username"]) if row["role"] == ADMIN else CustomerAccount(row)

    def limiter(self):
        return LoginRateLimiter(self.accounts(), self.settings.secret)

    async def login_account(self, address, body, admin_only=False):
        username, password = credentials(body)
        limiter = self.limiter()
        ticket = await limiter.claim(address)
        await self.bootstrap_admin()
        row = await self.accounts().find_by_username(username)
        digest = await self.derive(password, row["salt"] if row else "dummy-login-salt")
        if row and equal(digest, row["password_hash"]) and (not admin_only or row["role"] == ADMIN):
            await limiter.clear(ticket)
            user = AdministratorAccount(row["username"]) if row["role"] == ADMIN else CustomerAccount(row)
            return user.public()
        raise AccessError(401, "Tài khoản hoặc mật khẩu không đúng.")

    async def register_account(self, address, body):
        username, password = credentials(body)
        name = body.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if not name or text_length(name) > 80 or not re.fullmatch(r"[a-z0-9_]{3,32}", username) or text_length(password) < 6:
            raise ValidationError("Nhập họ tên, tên đăng nhập 3–32 ký tự hợp lệ và mật khẩu tối thiểu 6 ký tự.")
        limiter = self.limiter()
        ticket = await limiter.claim(address)
        repository = self.accounts()
        if username == (self.settings.username or "").lower() or await repository.find_by_username(username):
            raise ConflictError("Tên đăng nhập đã được sử dụng.")
        salt = str(uuid4())
        digest = await self.derive(password, salt)
        if not await repository.create(str(uuid4()), username, name, digest, salt):
            raise ConflictError("Tên đăng nhập đã được sử dụng.")
        await limiter.clear(ticket)

    async def save_customer_profile(self, identity, body):
        user = await self.current_account(identity)
        if not user or not user.has_role(CUSTOMER):
            raise AccessError(401, "Vui lòng đăng nhập tài khoản khách hàng.")
        profile = user.validate_update(body)
        await self.accounts().update_profile(user.id, profile)
        return {**user.public(), **profile}


class AccessPolicy:
    def __init__(self, actor):
        self.actor = actor

    def require_role(self, role):
        if self.actor is None:
            raise AccessError(401, "Vui lòng đăng nhập.")
        if not self.actor.has_role(role):
            raise AccessError(403, "Bạn không có quyền thực hiện thao tác này.")

    def booking_scope(self):
        if self.actor is None:
            raise AccessError(401, "Vui lòng đăng nhập.")
        return self.actor.booking_scope()


class BookingService:
    def __init__(self, repository: BookingPort, access: AccessPolicy, today: str):
        self.repository = repository
        self.access = access
        self.today = today

    async def bookings(self):
        return await self.repository.list_bookings(self.access.booking_scope())

    async def place_booking(self, body):
        self.access.require_role(CUSTOMER)
        request_id = required_text(body.get("requestId"), 80, "Mã yêu cầu", "requestId")
        booking_id = "MG" + sha256((self.access.actor.id + ":" + request_id).encode()).hexdigest().upper()
        booking = Booking.request(booking_id, self.access.actor.id, body)
        booking = replace(booking, unit_price=integer_between(
            body.get("expectedPrice"), 1, 1_000_000_000, "Giá đã xem", "expectedPrice"))
        if not await self.repository.place_booking(booking, self.today):
            raise ConflictError("Đợt khởi hành đã đóng hoặc không còn đủ chỗ.", "day")
        return {"id": booking_id}

    async def payment_history(self, booking_id):
        self.access.require_role(ADMIN)
        return await self.repository.payment_history(booking_id)

    async def update_booking(self, booking_id, action):
        actor = self.access.actor
        customer_cancel = action == "cancel" and actor is not None and actor.cancellation_owner() is not None
        rule = Booking.transition(action, customer_cancel)
        self.access.require_role(CUSTOMER if customer_cancel else ADMIN)
        owner_id = actor.id if customer_cancel else None
        if not await self.repository.update_booking(booking_id, rule, owner_id, self.today):
            raise ConflictError("Không thể thao tác với đơn ở trạng thái hoặc ngày khởi hành hiện tại.")


class TourCatalogService:
    def __init__(self, repository: TourCatalogPort, access: AccessPolicy, today: str):
        self.repository = repository
        self.access = access
        self.today = today

    async def catalog(self):
        actor = self.access.actor
        return await self.repository.catalog(actor is not None and actor.manages_catalog)

    async def save_tour(self, tour_id, body):
        self.access.require_role(ADMIN)
        tour = Tour.request(tour_id or str(uuid4()), body)
        if not await self.repository.save_tour(tour, not tour_id):
            raise AppError(404, "Không tìm thấy tour.")
        return {"id": tour.id}

    async def set_visibility(self, tour_id, hidden):
        self.access.require_role(ADMIN)
        if type(hidden) is not bool:
            raise ValidationError("Trạng thái hiển thị không hợp lệ.")
        if not await self.repository.set_visibility(tour_id, hidden):
            raise AppError(404, "Không tìm thấy tour.")

    async def save_departure(self, tour_id, body):
        self.access.require_role(ADMIN)
        departure = Departure(tour_id, body.get("day"), body.get("capacity"))
        departure.require_open_date(self.today)
        edit = body.get("edit")
        if edit is not None and type(edit) is not bool:
            raise ValidationError("Thao tác lịch không hợp lệ.")
        if edit:
            if not await self.repository.change_departure_capacity(departure):
                raise ConflictError("Đợt đã bị xóa hoặc sức chứa thấp hơn số chỗ đã giữ.", "capacity")
        elif not await self.repository.create_departure(departure):
            raise ConflictError("Ngày này đã có đợt khởi hành hoặc tour đã bị xóa.", "day")

    async def remove_departure(self, tour_id, value):
        self.access.require_role(ADMIN)
        if not await self.repository.remove_departure(tour_id, Departure.validate_day(value)):
            raise ConflictError("Đợt không tồn tại hoặc đã có lịch sử đặt chỗ.")


class ReportsService:
    def __init__(self, repository: ReportsPort, access: AccessPolicy, today: str):
        self.repository = repository
        self.access = access
        self.today = today

    async def load(self, params):
        self.access.require_role(ADMIN)
        start = calendar_day(params["from"], "Ngày bắt đầu không hợp lệ.", "from") if params.get("from") else "0001-01-01"
        end = calendar_day(params["to"], "Ngày kết thúc không hợp lệ.", "to") if params.get("to") else "9999-12-31"
        tour_id = params.get("tour") or ""
        if start > end or text_length(tour_id) > 70:
            raise ValidationError("Bộ lọc báo cáo không hợp lệ.")
        return await self.repository.load(start, end, tour_id, self.today)
