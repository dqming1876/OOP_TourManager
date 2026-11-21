CREATE TABLE tours (
  id TEXT PRIMARY KEY,
  price INTEGER NOT NULL CHECK (price BETWEEN 1 AND 1000000000),
  hidden INTEGER NOT NULL DEFAULT 0 CHECK (hidden IN (0,1)),
  content TEXT NOT NULL CHECK (json_valid(content))
);

CREATE TABLE departures (
  tour_id TEXT NOT NULL REFERENCES tours(id),
  day TEXT NOT NULL,
  capacity INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 100),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved BETWEEN 0 AND capacity),
  PRIMARY KEY (tour_id, day)
);

CREATE TABLE bookings (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES accounts(id),
  tour_id TEXT NOT NULL,
  day TEXT NOT NULL,
  title TEXT NOT NULL,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  adults INTEGER NOT NULL CHECK (adults > 0),
  children INTEGER NOT NULL CHECK (children >= 0),
  unit_price INTEGER NOT NULL CHECK (unit_price > 0),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','cancelled')),
  paid INTEGER NOT NULL DEFAULT 0 CHECK (paid IN (0,1) AND (paid = 0 OR status = 'confirmed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tour_id, day) REFERENCES departures(tour_id, day)
);

CREATE INDEX bookings_by_customer ON bookings(user_id, created_at);

-- Each trigger is part of the same atomic statement as the booking write.
CREATE TRIGGER reserve_booking_seats AFTER INSERT ON bookings
BEGIN
  UPDATE departures SET reserved = reserved + NEW.adults + NEW.children
  WHERE tour_id = NEW.tour_id AND day = NEW.day;
END;

CREATE TRIGGER release_booking_seats AFTER UPDATE OF status ON bookings
WHEN OLD.status <> 'cancelled' AND NEW.status = 'cancelled'
BEGIN
  UPDATE departures SET reserved = reserved - OLD.adults - OLD.children
  WHERE tour_id = OLD.tour_id AND day = OLD.day;
END;
