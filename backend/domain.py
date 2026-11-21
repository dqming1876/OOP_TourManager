"""Immutable business entities shared by the application and persistence layers."""

import re
from dataclasses import dataclass, replace
from datetime import date
from types import MappingProxyType

MAX_SAFE = 2**53 - 1
ADMIN = "admin"
CUSTOMER = "customer"


class AppError(Exception):
    def __init__(self, status, message, field=None):
        super().__init__(message)
        self.status = status
        self.field = field


class ValidationError(AppError):
    def __init__(self, message, field=None):
        super().__init__(400, message, field)


class AccessError(AppError):
    pass


class ConflictError(AppError):
    def __init__(self, message, field=None):
        super().__init__(409, message, field)


def text_length(value):
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def required_text(value, limit, label, field):
    if isinstance(value, str):
        value = value.strip()
        if value and text_length(value) <= limit:
            return value
    raise ValidationError(f"{label} không hợp lệ.", field)


def integer_between(value, low, high, label, field):
    if type(value) in (int, float) and low <= value <= high and int(value) == value:
        return int(value)
    raise ValidationError(f"{label} phải từ {low} đến {high}.", field)


def valid_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        # The ISO calendar used by the previous implementation includes year zero.
        if value.startswith("0000"):
            return valid_day("2000" + value[4:])
        return False
    return True


def calendar_day(value, message, field):
    if not valid_day(value):
        raise ValidationError(message, field)
    return value


def contact_phone(value, digits_pattern):
    return re.fullmatch(digits_pattern, value) and sum("0" <= c <= "9" for c in value) >= 8


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    username: str
    role: str

    def public(self):
        return {"id": self.id, "name": self.name, "username": self.username, "role": self.role}

    def booking_scope(self):
        return self.id


class AdministratorAccount(Account):
    def __init__(self, username):
        super().__init__("admin", "Quản trị viên", username, ADMIN)

    def booking_scope(self):
        return None


@dataclass(frozen=True, init=False)
class CustomerAccount(Account):
    profile: MappingProxyType

    def __init__(self, row):
        super().__init__(row["id"], row["name"], row["username"], CUSTOMER)
        object.__setattr__(self, "profile", MappingProxyType({
            key: row[key] for key in ("email", "phone", "address", "birthday")
        }))

    def public(self):
        return {**super().public(), **self.profile}

    def validate_update(self, body):
        profile = {}
        fields = {
            "name": ("Họ tên", 80), "email": ("Email", 120), "phone": ("Số điện thoại", 20),
            "address": ("Địa chỉ", 250), "birthday": ("Ngày sinh", 10),
        }
        for field, (label, limit) in fields.items():
            value = body.get(field)
            value = "" if value is None else value
            if not isinstance(value, str) or text_length(value.strip()) > limit:
                raise ValidationError(f"{label} không hợp lệ.", field)
            profile[field] = value.strip()
        if not profile["name"]:
            raise ValidationError("Họ tên không hợp lệ.", "name")
        if profile["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", profile["email"]):
            raise ValidationError("Email không hợp lệ.", "email")
        if profile["phone"] and not contact_phone(profile["phone"], r"[0-9+ ()-]+"):
            raise ValidationError("Số điện thoại không hợp lệ.", "phone")
        if profile["birthday"] and not valid_day(profile["birthday"]):
            raise ValidationError("Ngày sinh không hợp lệ.", "birthday")
        return profile


@dataclass(frozen=True)
class Departure:
    tour_id: str
    day: str
    capacity: int
    reserved: int = 0

    def __post_init__(self):
        self.validate_day(self.day)
        integer_between(self.capacity, 1, 100, "Sức chứa", "capacity")
        integer_between(self.reserved, 0, self.capacity, "Số chỗ đang giữ", "reserved")

    @staticmethod
    def validate_day(value):
        return calendar_day(value, "Ngày khởi hành không hợp lệ.", "day")

    def require_open_date(self, today):
        if self.day < today:
            raise ValidationError("Không thể sửa lịch đã qua.", "day")

    @property
    def remaining(self):
        return self.capacity - self.reserved


PENDING, CONFIRMED, CANCELLED = "pending", "confirmed", "cancelled"


@dataclass(frozen=True)
class Transition:
    before: str
    after: str
    paid: bool = False
    next_paid: bool = False
    check_day: bool = False
    also_from: str | None = None


TRANSITIONS = MappingProxyType({
    "confirm": Transition(PENDING, CONFIRMED, check_day=True),
    "collect": Transition(CONFIRMED, CONFIRMED, next_paid=True),
    "refund": Transition(CONFIRMED, CONFIRMED, paid=True),
    "cancel": Transition(PENDING, CANCELLED, also_from=CONFIRMED),
})


@dataclass(frozen=True)
class Booking:
    id: str
    user_id: str
    tour_id: str
    day: str
    name: str
    phone: str
    adults: int
    children: int
    title: str | None = None
    unit_price: int | None = None
    status: str = PENDING
    paid: bool = False

    def __post_init__(self):
        if self.status not in (PENDING, CONFIRMED, CANCELLED) or type(self.paid) is not bool or (
            self.paid and self.status != CONFIRMED
        ):
            raise ValidationError("Trạng thái đơn và thanh toán không tương thích.")
        integer_between(self.adults, 1, MAX_SAFE, "Số người lớn", "adults")
        integer_between(self.children, 0, MAX_SAFE, "Số trẻ em", "children")
        if self.unit_price is not None:
            integer_between(self.unit_price, 1, MAX_SAFE, "Giá chốt", "unitPrice")

    @classmethod
    def request(cls, booking_id, user_id, body):
        phone = required_text(body.get("phone"), 16, "Số điện thoại", "phone")
        if not contact_phone(phone, r"[0-9+ ()-]{9,16}"):
            raise ValidationError("Số điện thoại không hợp lệ.", "phone")
        return cls(
            booking_id, user_id, required_text(body.get("tourId"), 70, "Tour", "tourId"),
            Departure.validate_day(body.get("day")),
            required_text(body.get("name"), 80, "Tên người đại diện", "name"), phone,
            integer_between(body.get("adults"), 1, 100, "Số người lớn", "adults"),
            integer_between(body.get("children"), 0, 99, "Số trẻ em", "children"),
        )

    @staticmethod
    def transition(action, own_booking_only):
        if action not in TRANSITIONS:
            raise ValidationError("Thao tác đơn không hợp lệ.")
        rule = TRANSITIONS[action]
        return replace(rule, also_from=PENDING) if action == "cancel" and own_booking_only else rule

    @property
    def people(self):
        return self.adults + self.children

    @property
    def total(self):
        if self.unit_price is None:
            raise ConflictError("Đơn chưa có giá chốt.")
        return self.people * self.unit_price


@dataclass(frozen=True)
class PaymentEvent:
    date: str
    kind: str
    amount: int

    def __post_init__(self):
        calendar_day(self.date, "Ngày ghi nhận không hợp lệ.", "date")
        if self.kind not in ("collect", "refund"):
            raise ValidationError("Loại nghiệp vụ thanh toán không hợp lệ.")
        integer_between(self.amount, 1, MAX_SAFE, "Số tiền", "amount")

    @property
    def signed_amount(self):
        return -self.amount if self.kind == "refund" else self.amount


@dataclass(frozen=True)
class Destination:
    province: str
    name: str

    @classmethod
    def request(cls, province, name, field="place"):
        return cls(required_text(province, 80, "Tỉnh thành", "province"),
                   required_text(name, 120, "Điểm đến", field))


@dataclass(frozen=True)
class TourStop:
    day_number: int
    activity: str
    destination: Destination

    def write_row(self):
        return {"dayNumber": self.day_number, "place": self.destination.name, "activity": self.activity}


@dataclass(frozen=True)
class Tour:
    id: str
    details: MappingProxyType
    stops: tuple[TourStop, ...] | None

    @classmethod
    def request(cls, tour_id, body):
        destination = Destination.request(body.get("province"), body.get("place"))
        details = {
            "title": required_text(body.get("title"), 120, "Tên tour", "title"),
            "province": destination.province, "place": destination.name,
            "price": integer_between(body.get("price"), 1, 1_000_000_000, "Giá tour", "price"),
            "desc": required_text(body.get("desc"), 4000, "Mô tả", "desc"),
            "days": integer_between(body.get("days"), 1, 30, "Số ngày", "days"),
        }
        for key in ("category", "pickup", "includes", "excludes", "coverSource"):
            if js_truthy(body.get(key)):
                details[key] = required_text(body[key], 2000, key, key)
        cover = body.get("cover")
        if js_truthy(cover):
            if not isinstance(cover, str) or len(cover) > 1_398_134 or not re.fullmatch(
                r"data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}", cover
            ):
                raise ValidationError("Ảnh phải là JPG, PNG hoặc WebP tối đa 1 MB.", "cover")
            details["cover"] = cover
        if "itinerary" not in body:
            return cls(tour_id, MappingProxyType(details), None)
        itinerary = body["itinerary"]
        if not isinstance(itinerary, list) or len(itinerary) != details["days"]:
            raise ValidationError("Lịch trình phải có đủ nội dung mỗi ngày.")
        places = body.get("stops", [destination.name] * len(itinerary))
        if not isinstance(places, list) or len(places) != len(itinerary):
            raise ValidationError("Chọn điểm ghé cho từng ngày.")
        stops = tuple(TourStop(
            index + 1, required_text(activity, 2000, "Nội dung lịch trình", f"itinerary-{index}"),
            Destination.request(destination.province, places[index], f"stop-{index}"),
        ) for index, activity in enumerate(itinerary))
        return cls(tour_id, MappingProxyType(details), stops)


def js_truthy(value):
    return isinstance(value, (dict, list)) or bool(value)
