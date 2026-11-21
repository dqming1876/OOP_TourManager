import { AccountRole } from '../domain/account.js';
import { AppError } from '../domain/errors.js';
import { json, readObject, requirePost } from './http.js';

export async function operationsRoute(request, url, { catalog, bookings, reports, access }) {
  const [, , , resource, id, action, extra] = url.pathname.split('/');
  if (extra !== undefined) throw new AppError(404, 'Không tìm thấy chức năng.');
  if (request.method === 'GET' && !id) {
    if (resource === 'tours') return json({ tours: await catalog.catalog() });
    if (resource === 'bookings') return json({ bookings: await bookings.bookings() });
    if (resource === 'reports') {
      return json(await reports.load(url.searchParams));
    }
    throw new AppError(404, 'Không tìm thấy chức năng.');
  }
  if (request.method === 'GET' && resource === 'bookings' && id && action === 'payments') {
    return json({ payments: await bookings.paymentHistory(id) });
  }
  requirePost(request);
  const customerAction = resource === 'bookings' && (!id || (action === 'cancel' && access.actor?.role === AccountRole.CUSTOMER));
  access.requireRole(customerAction ? AccountRole.CUSTOMER : AccountRole.ADMIN);
  const body = await readObject(request, 3_000_000);
  if (resource === 'tours' && !action) return json(await catalog.saveTour(id, body), id ? 200 : 201);
  if (resource === 'tours' && id && action === 'visibility') await catalog.setVisibility(id, body.hidden);
  else if (resource === 'tours' && id && action === 'departures') await catalog.saveDeparture(id, body);
  else if (resource === 'tours' && id && action === 'remove-departure') await catalog.removeDeparture(id, body.day);
  else if (resource === 'bookings' && !id) return json(await bookings.placeBooking(body), 201);
  else if (resource === 'bookings' && action) await bookings.updateBooking(id, action);
  else throw new AppError(404, 'Không tìm thấy chức năng.');
  return json({ ok: true });
}
