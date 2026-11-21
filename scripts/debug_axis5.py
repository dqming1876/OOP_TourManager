"""Trace the real booking guard and HTTP call stack on the three-seat fixture."""

import argparse
import asyncio
import sys

from backend.repositories import BookingRepository
from tests.fixtures import GUEST, ORDER, api, cookie, last_seats


async def check(expected):
    worker = last_seats()
    db = worker.database
    observed = []

    def trace(frame, event, _arg):
        if event == "call" and frame.f_code is BookingRepository.place_booking.__code__:
            booking = frame.f_locals["booking"]
            if booking.id in {record[0] for record in observed}:
                return None
            departure = db.execute("SELECT capacity,reserved FROM departures WHERE tour_id=? AND day=?",
                                   (booking.tour_id, booking.day)).fetchone()
            stack, current = [], frame
            while current is not None:
                stack.append(current.f_code.co_name)
                if current.f_code.co_name == "operations_route":
                    break
                current = current.f_back
            observed.append((booking.id, stack, (booking.people, *departure)))
        return None

    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        reply = await api(worker, "/api/ops/bookings", ORDER, cookie(worker, GUEST))
    finally:
        sys.settrace(previous)
        db.close()
    assert reply.status == expected, (reply.status, expected)
    assert len(observed) == 1, observed
    _, stack, watch = observed[0]
    assert stack == ["place_booking", "place_booking", "operations_route"], stack
    assert watch == (3, 3, 0), watch
    print("Call Stack: BookingRepository.place_booking → BookingService.place_booking → operations_route")
    print(f"Watch: requested={watch[0]}, capacity={watch[1]}, reserved={watch[2]}. HTTP {reply.status}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status", nargs="?", default=201, type=int)
    asyncio.run(check(parser.parse_args().status))
