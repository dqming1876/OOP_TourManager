async function operationsApi(path, body) {
  const options = body === undefined ? { cache: 'no-store' } : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
  const response = await fetch('/api/ops/' + path, options);
  const result = await response.json();
  if (!response.ok) {
    const error = new Error(result.error || 'Không thể thực hiện thao tác.');
    error.field = result.field;
    throw error;
  }
  return result;
}

function vietnamDay(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
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
    dates: tour.departures.filter(item => item.day >= vietnamDay() && item.remaining > 0).map(item => item.day),
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
  form.querySelector('.submission-error').textContent = '';
  const fields = new FormData(form);
  const day = fields.get('day');
  const adults = Number(fields.get('adults'));
  const children = Number(fields.get('children'));
  const tour = tours.find(tour => tour.id === tourId);
  const available = remaining(tour, day);
  const capacityError = day && adults + children > available ? {
    day: 'Đợt này còn ' + available + ' chỗ. Chọn đợt khác hoặc giảm số khách.',
  } : {};
  if (!validateMingoForm(form, capacityError)) return;
  const button = form.querySelector('button[type="submit"]');
  if (button.disabled) return;
  button.disabled = true;
  const payload = { tourId, day, adults, children, name: fields.get('name'), phone: fields.get('phone'), expectedPrice: Number(form.dataset.price) };
  const signature = JSON.stringify({ userId: user.id, ...payload });
  // Keep the same key after a network failure; changed form contents create a new intent.
  if (form.dataset.signature !== signature) {
    form.dataset.signature = signature;
    form.dataset.requestId = crypto.randomUUID();
  }
  let receipt;
  try {
    receipt = await operationsApi('bookings', {
      ...payload, requestId: form.dataset.requestId,
    });
  } catch (error) {
    showSubmissionError(form, error);
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
