"""Stable camelCase DTOs used by the existing browser code."""


def booking_view(booking):
    return {
        "id": booking.id, "userId": booking.user_id, "tourId": booking.tour_id,
        "date": booking.day, "title": booking.title, "name": booking.name, "phone": booking.phone,
        "adults": booking.adults, "children": booking.children, "unitPrice": booking.unit_price,
        "status": booking.status, "paid": booking.paid, "people": booking.people, "total": booking.total,
    }


def departure_view(departure):
    return {"day": departure.day, "capacity": departure.capacity, "remaining": departure.remaining}


def payment_view(event):
    return {"date": event.date, "kind": event.kind, "amount": event.amount, "signedAmount": event.signed_amount}
