"""Trace itinerary composition, placement, and a rejected payment through the Python API."""

import asyncio
import json
import sys

from backend.domain import TourStop
from backend.repositories import BookingRepository
from backend.services import BookingService
from tests.fixtures import FUTURE, GUEST, ORDER, TOUR, api, cookie, last_seats


async def check():
    worker = last_seats()
    admin, guest = cookie(worker), cookie(worker, GUEST)
    recorded = {}

    def trace(frame, event, _arg):
        if event != "call":
            return None
        scope = frame.f_locals
        code = frame.f_code
        if code is TourStop.__init__.__code__:
            label, value = "tour-stop", scope["day_number"]
        elif code is BookingService.place_booking.__code__:
            label, value = "place-booking", scope["body"]["adults"] + scope["body"]["children"]
        elif code is BookingRepository.place_booking.__code__:
            label, value = "hold-seats", scope["booking"].people
        elif code is BookingRepository.update_booking.__code__:
            rule = scope["rule"]
            label, value = "payment-guard", (rule.before, rule.also_from, rule.next_paid, scope["owner_id"] is None)
        else:
            return None
        stack, current = [], frame
        while current is not None:
            stack.append(current.f_code.co_name)
            if current.f_code.co_name == "operations_route":
                break
            current = current.f_back
        recorded.setdefault(label, {})[value] = stack
        return None

    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        tour = await api(worker, "/api/ops/tours", TOUR, admin)
        assert tour.status == 201
        tour_id = json.loads(tour.body)["id"]
        slot = await api(worker, f"/api/ops/tours/{tour_id}/departures", {"day": FUTURE, "capacity": 3}, admin)
        assert slot.status == 200
        booking = await api(worker, "/api/ops/bookings", {**ORDER, "tourId": tour_id}, guest)
        assert booking.status == 201
        booking_id = json.loads(booking.body)["id"]
        collect = await api(worker, f"/api/ops/bookings/{booking_id}/collect", {}, admin)
        assert collect.status == 409
        assert worker.database.execute("SELECT paid FROM bookings WHERE id=?", (booking_id,)).fetchone()[0] == 0
        assert worker.database.execute("SELECT count(*) FROM payment_events").fetchone()[0] == 0
    finally:
        sys.settrace(previous)
        worker.database.close()
    assert {key: list(entries) for key, entries in recorded.items()} == {
        "tour-stop": [1, 2], "place-booking": [3], "hold-seats": [3],
        "payment-guard": [("confirmed", None, True, True)],
    }
    for key, entries in recorded.items():
        for value, stack in entries.items():
            assert "operations_route" in stack, stack
            print(f"{key} | {' → '.join(stack)} | Watch {value}")
    print("HTTP 409 khi thu đơn chờ; paid = 0, bút toán = 0.")


if __name__ == "__main__":
    asyncio.run(check())
