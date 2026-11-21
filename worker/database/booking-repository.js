import { Booking } from '../domain/booking.js';
import { PaymentEvent } from '../domain/payment-event.js';
import { bookingView, paymentView } from '../dto/operations.js';

/** @implements {import('../ports.js').BookingPort} */
export class BookingRepository {
  constructor(db) {
    this.db = db;
  }

  prepare(sql, ...values) {
    return this.db.prepare(sql).bind(...values);
  }

  async listBookings(userId) {
    const query = userId === null
      ? this.prepare('SELECT * FROM bookings ORDER BY created_at DESC, rowid DESC')
      : this.prepare('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC, rowid DESC', userId);
    const { results } = await query.all();
    return results.map(row => {
      const booking = new Booking({
        id: row.id, userId: row.user_id, tourId: row.tour_id, day: row.day,
        title: row.title, name: row.name, phone: row.phone, adults: row.adults, children: row.children,
        unitPrice: row.unit_price, status: row.status, paid: Boolean(row.paid),
      });
      return bookingView(booking);
    });
  }

  async paymentHistory(bookingId) {
    const { results } = await this.prepare(`
      SELECT recorded_on AS date, kind, amount FROM payment_events WHERE booking_id = ? ORDER BY id
    `, bookingId).all();
    return results.map(row => paymentView(new PaymentEvent(row)));
  }

  async placeBooking(booking, today) {
    const { id, userId, tourId, day, name, phone, adults, children, people } = booking;
    const result = await this.prepare(`
      INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price)
      SELECT ?,?,t.id,d.day,json_extract(t.content,'$.title'),?,?,?,?,t.price
      FROM departures d JOIN tours t ON t.id = d.tour_id
      WHERE t.id = ? AND d.day = ? AND d.day >= ? AND t.hidden = 0
        AND d.capacity - d.reserved >= ?
    `, id, userId, name, phone, adults, children, tourId, day, today, people).run();
    return result.meta.changes > 0;
  }

  async updateBooking(id, rule, ownerId, today) {
    // Recheck the transition against the current row in the same statement that
    // invokes the seat and payment triggers. No read-then-write window.
    const result = await this.prepare(`
      UPDATE bookings SET status = ?, paid = ?
      WHERE id = ? AND status IN (?, ?) AND paid = ?
        AND (? IS NULL OR user_id = ?)
        AND (? = 0 OR day >= ?)
    `, rule.to, Number(rule.nextPaid), id, rule.from, rule.alsoFrom ?? rule.from, Number(rule.paid),
    ownerId, ownerId, Number(Boolean(rule.checkDay)), today).run();
    return result.meta.changes === 1;
  }
}
