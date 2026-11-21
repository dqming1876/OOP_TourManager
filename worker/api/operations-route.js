import { ReportsRepository } from '../database/reports-repository.js';
import { ReportsService } from '../service/reports-service.js';
import { OperationsRepository } from '../database/operations-repository.js';
import { AccountRole } from '../domain/account.js';
import { AppError } from '../domain/errors.js';
import { currentAccount } from '../service/accounts-service.js';
import { TourOperations } from '../service/operations-service.js';
import { json, readObject, requirePost } from './http.js';

const localDay = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' });

export async function operationsRoute(request, env, url) {
  const [, , , resource, id, action, extra] = url.pathname.split('/');
  if (extra !== undefined) throw new AppError(404, 'Không tìm thấy chức năng.');
  const actor = await currentAccount(request, env);
  const repository = new OperationsRepository(env.DB);
  const service = new TourOperations(repository, actor, localDay.format(new Date()));
  if (request.method === 'GET' && !id) {
    if (resource === 'tours') return json({ tours: await service.catalog() });
    if (resource === 'bookings') return json({ bookings: await service.bookings() });
    if (resource === 'reports') {
      return json(await new ReportsService(service, new ReportsRepository(repository)).load(url.searchParams));
    }
    throw new AppError(404, 'Không tìm thấy chức năng.');
  }
  if (request.method === 'GET' && resource === 'bookings' && id && action === 'payments') {
    return json({ payments: await service.paymentHistory(id) });
  }
  requirePost(request);
  const customerAction = resource === 'bookings' && (!id || (action === 'cancel' && actor?.role === AccountRole.CUSTOMER));
  service.requireRole(customerAction ? AccountRole.CUSTOMER : AccountRole.ADMIN);
  const body = await readObject(request, 3_000_000);
  if (resource === 'tours' && !action) return json(await service.saveTour(id, body), id ? 200 : 201);
  if (resource === 'tours' && id && action === 'visibility') await service.setVisibility(id, body.hidden);
  else if (resource === 'tours' && id && action === 'departures') await service.saveDeparture(id, body);
  else if (resource === 'tours' && id && action === 'remove-departure') await service.removeDeparture(id, body.day);
  else if (resource === 'bookings' && !id) return json(await service.placeBooking(body), 201);
  else if (resource === 'bookings' && action) await service.updateBooking(id, action);
  else throw new AppError(404, 'Không tìm thấy chức năng.');
  return json({ ok: true });
}
