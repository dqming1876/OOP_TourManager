import { createSession, customerCookie } from '../../worker/service/session.js';
import { makeWorker } from '../local-worker.js';

export const customerId = 'axis5-guest';
export const tourId = 'axis5-tour';

export async function lastSeatsFixture() {
  const worker = await makeWorker({ seed: `
    INSERT INTO accounts (id,username,name,password_hash,salt)
    VALUES ('axis5-guest','axis5_guest','Khách thử','fixture-only','fixture-only');
    INSERT INTO tours (id,price,content)
    VALUES ('axis5-tour',500000,'{"title":"Tour thử trục 5"}');
  ` });
  const day = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  worker.db.prepare('INSERT INTO departures (tour_id,day,capacity) VALUES (?,?,3)').run(tourId, day);
  const cookie = (await createSession(customerCookie, worker.env.ADMIN_SESSION_SECRET, customerId)).split(';')[0];
  const origin = 'http://localhost';
  const placeBooking = () => worker.fetch(new Request(origin + '/api/ops/bookings', {
    method: 'POST', headers: { Origin: origin, Cookie: cookie },
    body: JSON.stringify({ tourId, day, name: 'Khách thử', phone: '0900000000', adults: 2, children: 1 }),
  }));
  const departure = () => worker.db.prepare('SELECT capacity,reserved FROM departures WHERE tour_id = ? AND day = ?')
    .get(tourId, day);
  return { ...worker, day, placeBooking, departure };
}
