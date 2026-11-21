/** @implements {import('../ports.js').ReportPort} */
export class ReportsRepository {
  constructor(db) {
    this.db = db;
  }

  async load({ from, to, tourId, today }) {
    const { db } = this;
    const query = (sql, ...args) => db.prepare(sql).bind(...args);
    const range = [from, to, tourId, tourId];
    const [cash, bookings, capacity] = await db.batch([
      query(`
        SELECT substr(p.recorded_on,1,7) AS month,
          SUM(CASE WHEN p.kind = 'collect' THEN p.amount ELSE 0 END) AS collected,
          SUM(CASE WHEN p.kind = 'refund' THEN p.amount ELSE 0 END) AS refunded
        FROM payment_events p JOIN bookings b ON b.id = p.booking_id
        WHERE p.recorded_on BETWEEN ? AND ? AND (? = '' OR b.tour_id = ?)
        GROUP BY month ORDER BY month
      `, ...range),
      query(`
        SELECT substr(b.day,1,7) AS month,
          CASE WHEN b.status = 'pending' AND b.day < ? THEN 'expired'
               WHEN b.status = 'confirmed' AND b.paid = 1 AND b.day < ? THEN 'completed'
               ELSE b.status END AS state,
          COUNT(*) AS orders, SUM(b.adults + b.children) AS guests
        FROM bookings b
        WHERE b.day BETWEEN ? AND ? AND (? = '' OR b.tour_id = ?)
        GROUP BY month, state ORDER BY month, state
      `, today, today, ...range),
      query(`
        SELECT d.day, json_extract(t.content,'$.title') AS tour, d.capacity,
          d.reserved AS reserved, d.capacity - d.reserved AS available
        FROM departures d JOIN tours t ON t.id = d.tour_id
        WHERE d.day BETWEEN ? AND ? AND (? = '' OR d.tour_id = ?)
        ORDER BY d.day, tour
      `, ...range),
    ]);
    return { cash: cash.results, bookings: bookings.results, capacity: capacity.results };
  }
}
