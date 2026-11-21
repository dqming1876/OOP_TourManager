async function operationsApi(path, body) {
  const options = body === undefined ? { cache: 'no-store' } : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
  const response = await fetch('/api/ops/' + path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Không thể thực hiện thao tác.');
  return result;
}

let operationsRefresh = 0;

async function refreshOperations({ includeBookings = false } = {}) {
  const refresh = ++operationsRefresh;
  const activeUser = user?.id;
  const [catalog, orders] = await Promise.all([
    operationsApi('tours'),
    includeBookings && activeUser ? operationsApi('bookings') : null,
  ]);
  if (refresh !== operationsRefresh || activeUser !== user?.id) return false;
  tours = catalog.tours.map(tour => ({
    ...tour,
    dates: tour.departures.map(item => item.day),
  }));
  bookings = orders?.bookings || [];
  return true;
}

async function loadPublicOperations() {
  const page = location.hash;
  if (page.startsWith('#admin')) return;
  try {
    if (await refreshOperations({ includeBookings: page.startsWith('#bookings') }) && location.hash === page) {
      render();
    }
  } catch {
    if (location.hash === page) toast('Không tải được dữ liệu tour hoặc đơn. Vui lòng tải lại trang.');
  }
}

async function placeOrder(event, tourId) {
  event.preventDefault();
  if (!user) return account();
  if (user.role !== 'customer') return toast('Vui lòng dùng tài khoản khách hàng để đặt tour.');
  const form = event.currentTarget;
  const fields = new FormData(form);
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  let receipt;
  try {
    receipt = await operationsApi('bookings', {
      tourId, day: $('#departure').value, adults: Number($('#people').value),
      children: Number($('#children').value), name: fields.get('name'), phone: fields.get('phone'),
    });
  } catch (error) {
    toast(error.message);
    return;
  } finally {
    button.disabled = false;
  }
  location.hash = 'bookings';
  modal('<h2>Đặt tour thành công</h2><p>Mã đơn: <strong>' + esc(receipt.id) +
    '</strong></p><p>Đơn đang chờ xác nhận.</p>');
}

async function performBookingAction(id, action) {
  if (action === 'cancel' && !confirm('Hủy đơn và trả lại chỗ?')) return;
  try {
    await operationsApi('bookings/' + id + '/' + action, {});
    await refreshOperations({ includeBookings: true });
    render();
    toast('Đã cập nhật đơn.');
  } catch (error) {
    toast(error.message);
  }
}

window.addEventListener('hashchange', loadPublicOperations);
loadPublicOperations();
restoreAccount();
