// Stable response shapes for the HTTP boundary.
export function bookingView(booking) {
  const { day: date, ...fields } = booking;
  return { ...fields, date, people: booking.people, total: booking.total };
}

export function departureView(departure) {
  return { day: departure.day, capacity: departure.capacity, remaining: departure.remaining };
}

export function paymentView(event) {
  return { date: event.date, kind: event.kind, amount: event.amount, signedAmount: event.signedAmount };
}
