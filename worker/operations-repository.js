class OperationsRepository {
  constructor(db) {
    this.db = db;
  }

  prepare(sql, ...values) {
    return this.db.prepare(sql).bind(...values);
  }

  async catalog(includeHidden) {
    const [tours, departures, stops] = await this.db.batch([
      this.prepare('SELECT * FROM tours WHERE hidden = 0 OR ? = 1 ORDER BY rowid', Number(includeHidden)),
      this.prepare('SELECT * FROM departures ORDER BY day'),
      this.prepare(`SELECT s.tour_id, s.activity, d.name AS place FROM tour_stops s
        JOIN destinations d ON d.id = s.destination_id ORDER BY s.day_number`),
    ]);
    const schedules = Map.groupBy(departures.results, row => row.tour_id);
    const itineraries = Map.groupBy(stops.results, row => row.tour_id);
    return tours.results.map(({ id, price, hidden, content }) => ({
      ...JSON.parse(content), id, price, hidden: Boolean(hidden),
      itinerary: (itineraries.get(id) || []).map(({ activity }) => activity),
      stops: (itineraries.get(id) || []).map(({ place }) => place),
      departures: (schedules.get(id) || []).map(row => ({
        day: row.day, capacity: row.capacity, remaining: row.capacity - row.reserved,
      })),
    }));
  }

  async listBookings(userId) {
    const query = userId === null
      ? this.prepare('SELECT * FROM bookings ORDER BY created_at DESC, rowid DESC')
      : this.prepare('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC, rowid DESC', userId);
    const { results } = await query.all();
    return results.map(row => ({
      id: row.id, userId: row.user_id, tourId: row.tour_id, date: row.day,
      title: row.title, name: row.name, phone: row.phone, adults: row.adults, children: row.children,
      people: row.adults + row.children, unitPrice: row.unit_price,
      total: (row.adults + row.children) * row.unit_price, status: row.status, paid: Boolean(row.paid),
    }));
  }

  async saveTour(id, tour, create) {
    const { price, itinerary, stops, ...content } = tour;
    if (!create && !await this.prepare('SELECT id FROM tours WHERE id = ?', id).first()) return false;
    const writeTour = create
      ? this.prepare('INSERT INTO tours (price, content, id) VALUES (?, ?, ?)', price, JSON.stringify(content), id)
      : this.prepare('UPDATE tours SET price = ?, content = ? WHERE id = ?', price, JSON.stringify(content), id);
    if (!itinerary) return (await writeTour.run()).meta.changes === 1;
    const details = JSON.stringify(itinerary.map((activity, index) => ({ place: stops[index], activity })));
    const destinations = this.prepare(`
      INSERT OR IGNORE INTO destinations (province,name)
      SELECT ?, json_extract(value,'$.place') FROM json_each(?)
    `, content.province, details);
    const rows = this.prepare(`
      INSERT INTO tour_stops (tour_id,day_number,destination_id,activity)
      SELECT ?,CAST(j.key AS INTEGER)+1,d.id,json_extract(j.value,'$.activity')
      FROM json_each(?) j JOIN destinations d ON d.province = ? AND d.name = json_extract(j.value,'$.place')
    `, id, details, content.province);
    await this.db.batch([writeTour, destinations, this.prepare('DELETE FROM tour_stops WHERE tour_id = ?', id), rows]);
    return true;
  }

  async paymentHistory(bookingId) {
    const { results } = await this.prepare(`
      SELECT recorded_on AS date, kind, amount FROM payment_events WHERE booking_id = ? ORDER BY id
    `, bookingId).all();
    return results;
  }

  async setVisibility(id, hidden) {
    const result = await this.prepare('UPDATE tours SET hidden = ? WHERE id = ?', Number(hidden), id).run();
    return result.meta.changes === 1;
  }

  async createDeparture(tourId, day, capacity) {
    const result = await this.prepare(`
      INSERT INTO departures (tour_id, day, capacity)
      SELECT id, ?, ? FROM tours WHERE id = ?
      ON CONFLICT(tour_id, day) DO NOTHING
    `, day, capacity, tourId).run();
    return result.meta.changes === 1;
  }

  async changeDepartureCapacity(tourId, day, capacity) {
    const result = await this.prepare(`
      UPDATE departures SET capacity = ?
      WHERE tour_id = ? AND day = ? AND reserved <= ?
    `, capacity, tourId, day, capacity).run();
    return result.meta.changes === 1;
  }

  async removeDeparture(tourId, day) {
    const result = await this.prepare(`
      DELETE FROM departures WHERE tour_id = ? AND day = ?
        AND NOT EXISTS (SELECT 1 FROM bookings WHERE tour_id = ? AND day = ?)
    `, tourId, day, tourId, day).run();
    return result.meta.changes === 1;
  }

  async placeBooking(id, userId, booking, today) {
    const { tourId, day, name, phone, adults, children } = booking;
    const result = await this.prepare(`
      INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price)
      SELECT ?,?,t.id,d.day,json_extract(t.content,'$.title'),?,?,?,?,t.price
      FROM departures d JOIN tours t ON t.id = d.tour_id
      WHERE t.id = ? AND d.day = ? AND d.day >= ? AND t.hidden = 0
        AND d.capacity - d.reserved >= ?
    `, id, userId, name, phone, adults, children, tourId, day, today, adults + children).run();
    return result.meta.changes > 0;
  }

  async updateBooking(id, action, ownerId) {
    const statements = {
      confirm: "UPDATE bookings SET status = 'confirmed' WHERE id = ? AND status = 'pending'",
      collect: "UPDATE bookings SET paid = 1 WHERE id = ? AND status = 'confirmed' AND paid = 0",
      refund: "UPDATE bookings SET paid = 0 WHERE id = ? AND status = 'confirmed' AND paid = 1",
      cancel: "UPDATE bookings SET status = 'cancelled' WHERE id = ? AND status <> 'cancelled' AND paid = 0",
    };
    const query = ownerId === null
      ? this.prepare(statements[action], id)
      : this.prepare(statements.cancel + " AND user_id = ? AND status = 'pending'", id, ownerId);
    return (await query.run()).meta.changes > 0;
  }
}
