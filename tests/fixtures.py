import json

from backend.app import Request
from backend.auth import ADMIN_COOKIE, CUSTOMER_COOKIE, create_session
from backend.domain import AdministratorAccount, CustomerAccount
from backend.services import AccessPolicy
from scripts.sqlite_worker import LocalWorker

TODAY = "2028-02-29"
FUTURE = "2028-03-07"
ORIGIN = "http://localhost"
ORDER = {
    "tourId": "axis5-tour", "day": FUTURE, "name": "Khách thử",
    "phone": "0900000000", "adults": 2, "children": 1,
}
TOUR = {
    "title": "Hà Nội", "province": "Hà Nội", "place": "Hồ Gươm",
    "price": 1_200_000, "desc": "Đi bộ và xem bảo tàng", "days": 2,
    "itinerary": ["Đi bộ", "Tham quan"], "stops": ["Hồ Gươm", "Bảo tàng Hà Nội"],
}
GUEST_ID = "axis5-guest"
OTHER_ID = "other-user"
ADMIN = AccessPolicy(AdministratorAccount("test_admin"))
GUEST = AccessPolicy(CustomerAccount(dict(
    id=GUEST_ID, name="Khách thử", username="axis5_guest", email="", phone="", address="", birthday="",
)))
OTHER = AccessPolicy(CustomerAccount({**GUEST.actor.public(), "id": OTHER_ID, "username": "other_user"}))


def last_seats():
    worker = LocalWorker(today=lambda: TODAY, seed="""
        INSERT INTO accounts (id,username,name,password_hash,salt) VALUES
          ('axis5-guest','axis5_guest','Khách thử','fixture-only','fixture-only'),
          ('other-user','other_user','Khách khác','fixture-only','fixture-only');
        INSERT INTO tours (id,price,content) VALUES ('axis5-tour',500000,'{"title":"Tour thử trục 5"}');
    """)
    worker.database.execute("INSERT INTO departures(tour_id,day,capacity) VALUES ('axis5-tour',?,3)", (FUTURE,))
    return worker


def cookie(worker, actor=ADMIN):
    name, identity = (ADMIN_COOKIE, None) if actor is ADMIN else (CUSTOMER_COOKIE, actor.actor.id)
    return create_session(name, worker.settings.secret, identity).split(";", 1)[0]


async def api(worker, path, body=None, token=None, *, origin=ORIGIN, method=None):
    headers = {"Origin": origin}
    if token:
        headers["Cookie"] = token
    return await worker.fetch(Request(method or ("GET" if body is None else "POST"),
                                      ORIGIN + path, headers, "" if body is None else json.dumps(body)))


REPORT_SEED = """
  INSERT INTO accounts (id,username,name,password_hash,salt)
  VALUES ('report-guest','report_guest','Khách thử','fixture-only','fixture-only');
  INSERT INTO tours (id,price,content) VALUES
    ('report-tour',750000,'{"title":"Tour báo cáo"}'),
    ('report-decoy',900000,'{"title":"Tour khác"}');
  INSERT INTO departures (tour_id,day,capacity) VALUES
    ('report-tour','2028-05-09',6),
    ('report-tour','2028-05-10',6),
    ('report-tour','2028-05-12',6),
    ('report-tour','2028-05-13',6),
    ('report-decoy','2028-05-11',6);
  INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price,status,paid) VALUES
    ('lower','report-guest','report-tour','2028-05-10','Tour báo cáo','Khách thử','0900000000',2,0,750000,'confirmed',1),
    ('cancelled','report-guest','report-tour','2028-05-12','Tour báo cáo','Khách thử','0900000000',1,0,1000000,'confirmed',0),
    ('upper','report-guest','report-tour','2028-05-12','Tour báo cáo','Khách thử','0900000000',2,1,750000,'pending',0),
    ('before','report-guest','report-tour','2028-05-09','Tour báo cáo','Khách thử','0900000000',1,0,400000,'confirmed',1),
    ('after','report-guest','report-tour','2028-05-13','Tour báo cáo','Khách thử','0900000000',1,0,600000,'confirmed',1),
    ('decoy','report-guest','report-decoy','2028-05-11','Tour khác','Khách thử','0900000000',1,0,900000,'confirmed',1);
  UPDATE bookings SET status = 'cancelled' WHERE id = 'cancelled';
  INSERT INTO payment_events (booking_id,recorded_on,kind,amount) VALUES
    ('lower','2028-05-10','collect',1500000),
    ('cancelled','2028-05-11','collect',1000000),
    ('cancelled','2028-05-12','refund',1000000),
    ('before','2028-05-09','collect',400000),
    ('after','2028-05-13','collect',600000),
    ('decoy','2028-05-11','collect',900000);
"""
