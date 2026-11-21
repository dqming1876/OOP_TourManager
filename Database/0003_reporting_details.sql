CREATE TABLE destinations (
  id INTEGER PRIMARY KEY,
  province TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE (province, name)
);

CREATE TABLE tour_stops (
  tour_id TEXT NOT NULL REFERENCES tours(id),
  day_number INTEGER NOT NULL CHECK (day_number BETWEEN 1 AND 30),
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  activity TEXT NOT NULL CHECK (length(activity) BETWEEN 1 AND 2000),
  PRIMARY KEY (tour_id, day_number)
);

INSERT OR IGNORE INTO destinations (province, name)
SELECT json_extract(content,'$.province'), json_extract(content,'$.place') FROM tours;

INSERT INTO tour_stops (tour_id, day_number, destination_id, activity)
SELECT t.id, CAST(j.key AS INTEGER) + 1, d.id, j.value
FROM tours t JOIN json_each(t.content,'$.itinerary') j
JOIN destinations d ON d.province = json_extract(t.content,'$.province')
AND d.name = json_extract(t.content,'$.place');

UPDATE tours SET content = json_remove(content,'$.itinerary');

CREATE TABLE payment_events (
  id INTEGER PRIMARY KEY,
  booking_id TEXT NOT NULL REFERENCES bookings(id),
  recorded_on TEXT NOT NULL DEFAULT (date('now','+7 hours')),
  kind TEXT NOT NULL CHECK (kind IN ('collect','refund')),
  amount INTEGER NOT NULL CHECK (amount > 0)
);

CREATE INDEX payment_events_by_day ON payment_events(recorded_on, booking_id);
CREATE INDEX payment_events_by_booking ON payment_events(booking_id, id);
CREATE INDEX bookings_by_departure ON bookings(tour_id, day, status);

-- Preserve an opening balance if a database already has paid bookings.
INSERT INTO payment_events (booking_id, kind, amount)
SELECT id, 'collect', (adults + children) * unit_price FROM bookings WHERE paid = 1;

CREATE TRIGGER record_payment_change AFTER UPDATE OF paid ON bookings
WHEN OLD.paid <> NEW.paid
BEGIN
  INSERT INTO payment_events (booking_id, kind, amount)
  VALUES (NEW.id, CASE NEW.paid WHEN 1 THEN 'collect' ELSE 'refund' END,
          (NEW.adults + NEW.children) * NEW.unit_price);
END;
