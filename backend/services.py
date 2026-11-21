"""Business services depend on ports, independent of HTTP and D1."""

import re
from time import monotonic
from uuid import uuid4

from .auth import ADMIN_COOKIE, CUSTOMER_COOKIE, Settings, derive_password, equal, session_identity
from .domain import (
    ADMIN, CUSTOMER, AccessError, AdministratorAccount, AppError, Booking, ConflictError,
    CustomerAccount, Departure, Tour, ValidationError, calendar_day, text_length,
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
    def __init__(self, repository: AccountsPort | None, settings: Settings, attempts, derive=derive_password):
        self.repository = repository
        self.settings = settings
        self.attempts = attempts
        self.derive = derive

    def accounts(self):
        if self.repository is None:
            raise AppError(503, "Hệ thống tài khoản chưa sẵn sàng.")
        return self.repository

    async def current_account(self, request):
        if session_identity(request, self.settings.secret, ADMIN_COOKIE):
            return AdministratorAccount(self.settings.username)
        account_id = session_identity(request, self.settings.secret, CUSTOMER_COOKIE)
        row = await self.repository.find_public(account_id) if account_id and self.repository else None
        return CustomerAccount(row) if row else None

    def record_attempt(self, request):
        key = request.header("CF-Connecting-IP") or "unknown"
        now = monotonic()
        while self.attempts:
            oldest = next(iter(self.attempts))
            if self.attempts[oldest][1] > now:
                break
            del self.attempts[oldest]
        count, until = self.attempts.get(key, (0, now + 300))
        if count >= 12:
            raise AppError(429, "Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 5 phút.")
        self.attempts[key] = (count + 1, until)
        return key

    async def login_account(self, request, body, admin_only=False):
        username, password = credentials(body)
        key = self.record_attempt(request)
        settings = self.settings
        if username == (settings.username or "").lower():
            if not (settings.salt and settings.password_hash and settings.secret):
                raise AppError(503, "Tài khoản quản trị chưa được cấu hình.")
            if equal(await self.derive(password, settings.salt), settings.password_hash):
                self.attempts.pop(key, None)
                return AdministratorAccount(settings.username).public(), ADMIN_COOKIE
        elif not admin_only:
            row = await self.accounts().find_by_username(username)
            digest = await self.derive(password, row["salt"] if row else "dummy-login-salt")
            if row and equal(digest, row["password_hash"]):
                self.attempts.pop(key, None)
                return CustomerAccount(row).public(), CUSTOMER_COOKIE
        raise AccessError(401, "Tài khoản hoặc mật khẩu không đúng.")

    async def register_account(self, request, body):
        username, password = credentials(body)
        name = body.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if not name or text_length(name) > 80 or not re.fullmatch(r"[a-z0-9_]{3,32}", username) or text_length(password) < 6:
            raise ValidationError("Nhập họ tên, tên đăng nhập 3–32 ký tự hợp lệ và mật khẩu tối thiểu 6 ký tự.")
        key = self.record_attempt(request)
        repository = self.accounts()
        if username == (self.settings.username or "").lower() or await repository.find_by_username(username):
            raise ConflictError("Tên đăng nhập đã được sử dụng.")
        salt = str(uuid4())
        digest = await self.derive(password, salt)
        if not await repository.create(str(uuid4()), username, name, digest, salt):
            raise ConflictError("Tên đăng nhập đã được sử dụng.")
        self.attempts.pop(key, None)

    async def save_customer_profile(self, request, body):
        user = await self.current_account(request)
        if not user or user.role != CUSTOMER:
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
        if self.actor.role != role:
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
        booking_id = "MG" + uuid4().hex.upper()
        booking = Booking.request(booking_id, self.access.actor.id, body)
        if not await self.repository.place_booking(booking, self.today):
            raise ConflictError("Đợt khởi hành đã đóng hoặc không còn đủ chỗ.", "day")
        return {"id": booking_id}

    async def payment_history(self, booking_id):
        self.access.require_role(ADMIN)
        return await self.repository.payment_history(booking_id)

    async def update_booking(self, booking_id, action):
        actor = self.access.actor
        customer_cancel = action == "cancel" and actor is not None and actor.role == CUSTOMER
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
        return await self.repository.catalog(actor is not None and actor.role == ADMIN)

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
