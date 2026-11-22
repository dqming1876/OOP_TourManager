"""Persistence adapters for the D1 binding and the local SQLite demo."""

import json
from collections import defaultdict

from .domain import Booking, Departure, PaymentEvent, ConflictError
from .views import booking_view, departure_view, payment_view


class AccountsRepository:
    def __init__(self, db):
        self.db = db

    async def find_public(self, account_id):
        return await self.db.first(
            "SELECT id, username, name, email, phone, address, birthday FROM accounts WHERE id = ?", account_id
        )

    async def find_by_username(self, username):
        return await self.db.first("SELECT * FROM accounts WHERE username = ?", username)

    async def create(self, account_id, username, name, password_hash, salt):
        return await self.db.execute("""
            INSERT INTO accounts (id, username, name, password_hash, salt) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO NOTHING
        """, account_id, username, name, password_hash, salt) == 1

    async def update_profile(self, account_id, profile):
        await self.db.execute(
            "UPDATE accounts SET name = ?, email = ?, phone = ?, address = ?, birthday = ? WHERE id = ?",
            *(profile[field] for field in ("name", "email", "phone", "address", "birthday")), account_id,
        )


class BookingRepository:
    def __init__(self, db):
        self.db = db

    async def list_bookings(self, user_id):
        if user_id is None:
            rows = await self.db.all("SELECT * FROM bookings ORDER BY created_at DESC, rowid DESC")
        else:
            rows = await self.db.all(
                "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC, rowid DESC", user_id
            )
        return [booking_view(Booking(
            row["id"], row["user_id"], row["tour_id"], row["day"], row["name"], row["phone"],
            row["adults"], row["children"], row["title"], row["unit_price"], row["status"], bool(row["paid"]),
        )) for row in rows]

    async def payment_history(self, booking_id):
        rows = await self.db.all("""
            SELECT recorded_on AS date, kind, amount FROM payment_events WHERE booking_id = ? ORDER BY id
        """, booking_id)
        return [payment_view(PaymentEvent(**row)) for row in rows]

    async def place_booking(self, booking, today):
        # The primary key and seat trigger make retries atomic, including across isolates.
        inserted = await self.db.execute("""
            INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price)
            SELECT ?,?,t.id,d.day,json_extract(t.content,'$.title'),?,?,?,?,t.price
            FROM departures d JOIN tours t ON t.id = d.tour_id
            WHERE t.id = ? AND d.day = ? AND d.day >= ? AND t.hidden = 0
              AND d.capacity - d.reserved >= ? AND t.price = ?
            ON CONFLICT(id) DO NOTHING
        """, booking.id, booking.user_id, booking.name, booking.phone, booking.adults,
            booking.children, booking.tour_id, booking.day, today, booking.people, booking.unit_price)
        if inserted:
            return True
        previous = await self.db.first("SELECT * FROM bookings WHERE id = ?", booking.id)
        if previous:
            fields = ("user_id", "tour_id", "day", "name", "phone", "adults", "children", "unit_price")
            if all(previous[key] == getattr(booking, key) for key in fields):
                return True
            raise ConflictError("Mã yêu cầu đã được dùng cho nội dung khác. Vui lòng mở lại trang đặt tour.")
        tour = await self.db.first("SELECT price FROM tours WHERE id = ?", booking.tour_id)
        if tour and tour["price"] != booking.unit_price:
            raise ConflictError("Giá tour đã thay đổi. Vui lòng tải lại trang và xác nhận giá mới.", "expectedPrice")
        return False

    async def update_booking(self, booking_id, rule, owner_id, today):
        return await self.db.execute("""
            UPDATE bookings SET status = ?, paid = ?
            WHERE id = ? AND status IN (?, ?) AND paid = ?
              AND (? = 1 OR user_id = ?)
              AND (? = 0 OR day >= ?)
        """, rule.after, int(rule.next_paid), booking_id, rule.before, rule.also_from or rule.before,
            int(rule.paid), int(owner_id is None), owner_id or "", int(rule.check_day), today) == 1


class ReportsRepository:
    def __init__(self, db):
        self.db = db

    async def load(self, start, end, tour_id, today):
        bounds = (start, end, tour_id, tour_id)
        cash, bookings, capacity = await self.db.batch([
            ("""
                SELECT substr(p.recorded_on,1,7) AS month,
                  SUM(CASE WHEN p.kind = 'collect' THEN p.amount ELSE 0 END) AS collected,
                  SUM(CASE WHEN p.kind = 'refund' THEN p.amount ELSE 0 END) AS refunded
                FROM payment_events p JOIN bookings b ON b.id = p.booking_id
                WHERE p.recorded_on BETWEEN ? AND ? AND (? = '' OR b.tour_id = ?)
                GROUP BY month ORDER BY month
            """, bounds),
            ("""
                SELECT substr(b.day,1,7) AS month,
                  CASE WHEN b.status = 'pending' AND b.day < ? THEN 'expired'
                       WHEN b.status = 'confirmed' AND b.paid = 1 AND b.day < ? THEN 'completed'
                       ELSE b.status END AS state,
                  COUNT(*) AS orders, SUM(b.adults + b.children) AS guests
                FROM bookings b
                WHERE b.day BETWEEN ? AND ? AND (? = '' OR b.tour_id = ?)
                GROUP BY month, state ORDER BY month, state
            """, (today, today, *bounds)),
            ("""
                SELECT d.day, json_extract(t.content,'$.title') AS tour, d.capacity,
                  d.reserved AS reserved, d.capacity - d.reserved AS available
                FROM departures d JOIN tours t ON t.id = d.tour_id
                WHERE d.day BETWEEN ? AND ? AND (? = '' OR d.tour_id = ?)
                ORDER BY d.day, tour
            """, bounds),
        ])
        return {"cash": cash, "bookings": bookings, "capacity": capacity}


class TourCatalogRepository:
    def __init__(self, db):
        self.db = db

    async def catalog(self, include_hidden):
        visibility = (int(include_hidden),)
        tours, departures, stops = await self.db.batch([
            ("SELECT * FROM tours WHERE hidden = 0 OR ? = 1 ORDER BY rowid", visibility),
            ("""
                SELECT d.* FROM departures d JOIN tours t ON t.id = d.tour_id
                WHERE t.hidden = 0 OR ? = 1 ORDER BY d.day
            """, visibility),
            ("""
                SELECT s.tour_id, s.activity, d.name AS place FROM tour_stops s
                JOIN destinations d ON d.id = s.destination_id JOIN tours t ON t.id = s.tour_id
                WHERE t.hidden = 0 OR ? = 1 ORDER BY s.day_number
            """, visibility),
        ])
        schedules = defaultdict(list)
        itineraries = defaultdict(list)
        for row in departures:
            schedules[row["tour_id"]].append(departure_view(Departure(
                row["tour_id"], row["day"], row["capacity"], row["reserved"]
            )))
        for row in stops:
            itineraries[row["tour_id"]].append(row)
        return [{
            **json.loads(row["content"]), "id": row["id"], "price": row["price"], "hidden": bool(row["hidden"]),
            "itinerary": [stop["activity"] for stop in itineraries[row["id"]]],
            "stops": [stop["place"] for stop in itineraries[row["id"]]],
            "departures": schedules[row["id"]],
        } for row in tours]

    async def save_tour(self, tour, create):
        if not create and not await self.db.first("SELECT id FROM tours WHERE id = ?", tour.id):
            return False
        content = dict(tour.details)
        price = content.pop("price")
        write = "INSERT INTO tours (price, content, id) VALUES (?, ?, ?)" if create else (
            "UPDATE tours SET price = ?, content = ? WHERE id = ?"
        )
        params = (price, json.dumps(content, ensure_ascii=True), tour.id)
        if tour.stops is None:
            return await self.db.execute(write, *params) == 1
        details = json.dumps([stop.write_row() for stop in tour.stops], ensure_ascii=True)
        await self.db.batch([
            (write, params),
            ("""
                INSERT OR IGNORE INTO destinations (province,name)
                SELECT ?, json_extract(value,'$.place') FROM json_each(?)
            """, (content["province"], details)),
            ("DELETE FROM tour_stops WHERE tour_id = ?", (tour.id,)),
            ("""
                INSERT INTO tour_stops (tour_id,day_number,destination_id,activity)
                SELECT ?,json_extract(j.value,'$.dayNumber'),d.id,json_extract(j.value,'$.activity')
                FROM json_each(?) j JOIN destinations d
                ON d.province = ? AND d.name = json_extract(j.value,'$.place')
            """, (tour.id, details, content["province"])),
        ])
        return True

    async def set_visibility(self, tour_id, hidden):
        return await self.db.execute(
            "UPDATE tours SET hidden = ? WHERE id = ?", int(hidden), tour_id
        ) == 1

    async def create_departure(self, departure):
        return await self.db.execute("""
            INSERT INTO departures (tour_id, day, capacity)
            SELECT id, ?, ? FROM tours WHERE id = ?
            ON CONFLICT(tour_id, day) DO NOTHING
        """, departure.day, departure.capacity, departure.tour_id) == 1

    async def change_departure_capacity(self, departure):
        return await self.db.execute("""
            UPDATE departures SET capacity = ?
            WHERE tour_id = ? AND day = ? AND reserved <= ?
        """, departure.capacity, departure.tour_id, departure.day, departure.capacity) == 1

    async def remove_departure(self, tour_id, day):
        return await self.db.execute("""
            DELETE FROM departures WHERE tour_id = ? AND day = ?
              AND NOT EXISTS (SELECT 1 FROM bookings WHERE tour_id = ? AND day = ?)
        """, tour_id, day, tour_id, day) == 1
