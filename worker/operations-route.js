async function operationsRoute(request, env, path) {
  try {
    const { method } = request;
    if (method !== 'GET' && method !== 'POST') throw new OperationError(405, 'Phương thức không hợp lệ.');
    if (method === 'POST' && request.headers.get('Origin') !== new URL(request.url).origin) {
      throw new OperationError(403, 'Nguồn yêu cầu không hợp lệ.');
    }
    const actor = await currentAccount(request, env);
    const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date());
    const service = new TourOperations(new OperationsRepository(env.DB), actor, today);
    const [, resource, id, action] = path.replace('/api/ops', '').split('/');
    if (method === 'GET' && !id) {
      if (resource === 'tours') return json({ tours: await service.catalog() });
      if (resource === 'bookings') return json({ bookings: await service.bookings() });
    }
    if (method === 'POST') {
      service.requireRole(resource === 'bookings' && (!id || (action === 'cancel' && actor?.role === 'customer'))
        ? 'customer' : 'admin');
      let body;
      try {
        const raw = await request.text();
        if (raw.length > 3_000_000) throw new OperationError(413, 'Dữ liệu quá lớn.');
        body = JSON.parse(raw);
        if (!body || Array.isArray(body) || typeof body !== 'object') throw new SyntaxError();
      } catch (error) {
        if (error instanceof OperationError) throw error;
        throw new OperationError(400, 'Dữ liệu không hợp lệ.');
      }
      if (resource === 'tours' && !action) return json(await service.saveTour(id, body), id ? 200 : 201);
      if (resource === 'tours' && id && action === 'visibility') await service.setVisibility(id, body.hidden);
      else if (resource === 'tours' && id && action === 'departures') await service.saveDeparture(id, body);
      else if (resource === 'tours' && id && action === 'remove-departure') await service.removeDeparture(id, body.day);
      else if (resource === 'bookings' && !id) return json(await service.placeBooking(body), 201);
      else if (resource === 'bookings' && action) await service.updateBooking(id, action);
      else throw new OperationError(404, 'Không tìm thấy chức năng.');
      return json({ ok: true });
    }
    return json({ error: 'Không tìm thấy chức năng.' }, 404);
  } catch (error) {
    if (error instanceof OperationError) return json({ error: error.message }, error.status);
    console.error('Tour operations failed', error.message);
    return json({ error: 'Không thể xử lý yêu cầu lúc này.' }, 500);
  }
}
