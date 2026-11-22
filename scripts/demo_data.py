"""Create the same catalog, departures, bookings and payment history as the previous demo."""

from datetime import date
from secrets import token_hex

from backend.app import local_day
from backend.auth import password_hash

DEMO_PASSWORD = "MingoDemo26!"
CUSTOMERS = (
    "Nguyễn An", "Trần Hải", "Lê Ngọc Mai", "Phạm Quỳnh", "Vũ Minh Châu",
    "Bùi Gia Hưng", "Đặng Thanh Trúc", "Đỗ Hoàng Sơn",
)
TOURS = (
    ("demo-hanoi", "Hà Nội – Phố cổ và Hồ Gươm", "Hà Nội", 1_200_000,
     ("Hồ Hoàn Kiếm", "Văn Miếu"),
     ("Đi bộ quanh hồ và khám phá phố cổ", "Tham quan Văn Miếu và làng nghề")),
    ("demo-hue", "Huế – Di sản bên sông Hương", "Thành phố Huế", 1_800_000,
     ("Đại Nội Huế", "Chùa Thiên Mụ"),
     ("Tìm hiểu Đại Nội và ẩm thực Huế", "Thăm chùa, đi thuyền dọc sông Hương")),
    ("demo-dalat", "Đà Lạt – Đồi thông và hồ", "Lâm Đồng", 2_400_000,
     ("Hồ Xuân Hương", "Hồ Tuyền Lâm"),
     ("Dạo ven hồ, ghé chợ Đà Lạt", "Đi bộ ven rừng và ngắm Hồ Tuyền Lâm")),
)
HISTORICAL = ((2, 0, "paid"), (2, 0, "pending"), (1, 0, "refunded"), (2, 0, "confirmed"))
NEXT_MONTH = ((2, 0, "paid"), (2, 0, "pending"), (1, 0, "paid"), (2, 0, "confirmed"))
EXTRA = (
    (1, 0, "pending"), (2, 1, "paid"), (1, 1, "confirmed"), (2, 0, "cancelled"),
    (3, 1, "paid"), (1, 0, "refunded"), (2, 2, "confirmed"), (1, 2, "pending"),
    (4, 0, "paid"), (2, 1, "pending"),
)


def quote(value):
    return "'" + value.replace("'", "''") + "'" if isinstance(value, str) else str(value)


def demo_sql(today=None):
    today = today or local_day()
    now = date.fromisoformat(today)

    def day(offset, number):
        year, month = divmod(now.year * 12 + now.month - 1 + offset, 12)
        return date(year, month + 1, number).isoformat()

    queries = []

    def insert(table, columns, *values, ignore=False):
        command = "INSERT OR IGNORE" if ignore else "INSERT"
        queries.append(f"{command} INTO {table} ({columns}) VALUES ({','.join(map(quote, values))});")

    for index, name in enumerate(CUSTOMERS):
        salt = token_hex(16)
        insert("accounts", "id,username,name,password_hash,salt,email", f"demo-c{index}",
               f"mingo_khach{index + 1}", name, password_hash(DEMO_PASSWORD, salt), salt,
               f"mingo-khach{index + 1}@example.invalid")

    for tour_index, (tour_id, title, province, price, stops, activities) in enumerate(TOURS):
        insert("tours", "id,price,title,province,place,days,desc", tour_id, price,
               title, province, stops[0], 2, ". ".join(activities))
        for index, (place, activity) in enumerate(zip(stops, activities), start=1):
            insert("destinations", "province,name", province, place, ignore=True)
            queries.append(f"""
                INSERT INTO tour_stops (tour_id,day_number,destination_id,activity)
                SELECT {quote(tour_id)},{index},id,{quote(activity)} FROM destinations
                WHERE province = {quote(province)} AND name = {quote(place)};
            """)
        booked_this_month = min(day(0, 3 + tour_index), today)
        departures = (
            (day(-2, 12 + tour_index), day(-2, 5 + tour_index), 8, HISTORICAL),
            (day(-1, 12 + tour_index), day(-1, 5 + tour_index), 8, HISTORICAL),
            (day(1, 12 + tour_index), day(1, 5 + tour_index), 8, NEXT_MONTH),
            (day(-3, 22 + tour_index), day(-3, 3 + tour_index), 30, EXTRA),
            (day(0, 22 + tour_index), booked_this_month, 28, EXTRA),
            (day(2, 22 + tour_index), booked_this_month, 24, EXTRA),
        )
        for period, (departure, event_day, capacity, orders) in enumerate(departures):
            insert("departures", "tour_id,day,capacity", tour_id, departure, capacity)
            for index, (adults, children, outcome) in enumerate(orders):
                booking_id = f"MGDEMO{tour_index}{period}{index}"
                customer = (tour_index + period + index) % len(CUSTOMERS)
                insert("bookings", "id,user_id,tour_id,day,title,name,phone,adults,children,unit_price,created_at",
                       booking_id, f"demo-c{customer}", tour_id, departure, title, CUSTOMERS[customer],
                       f"09000000{customer:02}", adults, children, price, event_day + " 09:00:00")
                updates = {
                    "paid": ("status = 'confirmed', paid = 1",),
                    "refunded": ("status = 'confirmed', paid = 1", "paid = 0, status = 'cancelled'"),
                    "confirmed": ("status = 'confirmed'",),
                    "cancelled": ("status = 'cancelled'",),
                }
                for update in updates.get(outcome, ()):
                    queries.append(f"UPDATE bookings SET {update} WHERE id = {quote(booking_id)};")
                if outcome in ("paid", "refunded"):
                    queries.append(f"UPDATE payment_events SET recorded_on = {quote(event_day)} "
                                   f"WHERE booking_id = {quote(booking_id)};")
    return "\n".join(queries) + "\n"
