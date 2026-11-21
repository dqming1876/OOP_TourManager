-- Tour stops belong to a tour. Destinations are shared and survive deleting a tour.
CREATE TABLE tour_stops_owned (
  tour_id TEXT NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
  day_number INTEGER NOT NULL CHECK (day_number BETWEEN 1 AND 30),
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  activity TEXT NOT NULL CHECK (length(activity) BETWEEN 1 AND 2000),
  PRIMARY KEY (tour_id, day_number)
);

INSERT INTO tour_stops_owned SELECT tour_id, day_number, destination_id, activity FROM tour_stops;
DROP TABLE tour_stops;
ALTER TABLE tour_stops_owned RENAME TO tour_stops;
