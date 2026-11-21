const adminTabs = {
  overview: 'Tổng quan',
  tours: 'Quản lý tour',
  departures: 'Lịch khởi hành',
  bookings: 'Xử lý đơn',
  payments: 'Thu tiền / hoàn tiền',
  destinations: 'Điểm đến',
};

function admin() {
  const nav = Object.entries(adminTabs).map(([id, label]) =>
    `<button class="${adminTab === id ? 'active' : ''}" onclick="showAdminTab('${id}')">${label}</button>`);
  return `<section class="wrap">
    <div class="eyebrow">MINGO / QUẢN TRỊ</div>
    <div class="section-head"><h1 style="font-size:40px">Quản lý hành trình</h1>
    <button class="outline" onclick="adminLogout()">Đăng xuất Admin</button></div>
    <div class="admin-shell"><aside class="admin-nav">${nav.join('')}</aside><div id="admin-content">${adminContent()}</div></div>
  </section>`;
}

function showAdminTab(tab) {
  adminTab = tab;
  $('#app').innerHTML = admin();
}

function adminContent() {
  if (adminTab === 'tours') return tourManagement();
  if (adminTab === 'departures') return departureManagement();
  if (adminTab === 'bookings') return bookingManagement(false);
  if (adminTab === 'payments') return bookingManagement(true);
  if (adminTab === 'destinations') {
    return `<h2>Quản lý địa danh và đặc sản</h2><p class="muted">Thay đổi ở mục này lưu trên trình duyệt.</p>
      <label>Chọn tỉnh<select id="edit-province" onchange="destinationEditor(this.value)">
        <option value="">Chọn tỉnh thành</option>
        ${PROVINCES.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('')}
      </select></label><div id="destination-editor"></div>`;
  }
  const revenue = bookings.filter(b => b.paid).reduce((sum, b) => sum + b.total, 0);
  return `<h2>Tổng quan</h2><div class="metrics">
    <div class="metric"><small>Tour đang bán</small><b>${tours.filter(t => !t.hidden).length}</b></div>
    <div class="metric"><small>Đơn chờ xác nhận</small><b>${bookings.filter(b => b.status === 'pending').length}</b></div>
    <div class="metric"><small>Tiền đã thu</small><b>${money(revenue)}</b></div>
  </div>`;
}

function adminFilters(placeholder, options) {
  return `<div class="toolbar">
    <input id="admin-search" aria-label="Tìm kiếm" placeholder="${placeholder}" oninput="filterAdminRows()">
    <select id="admin-status" aria-label="Lọc trạng thái" onchange="filterAdminRows()">
      <option value="">Tất cả trạng thái</option>${options.map(s => `<option>${s}</option>`).join('')}
    </select>
    <button type="button" class="outline" onclick="clearAdminFilters()">Xóa lọc</button>
  </div>`;
}

function clearAdminFilters() {
  $('#admin-search').value = '';
  $('#admin-status').value = '';
  filterAdminRows();
}

function filterAdminRows() {
  const query = $('#admin-search').value.trim().toLocaleLowerCase('vi');
  const status = $('#admin-status').value;
  document.querySelectorAll('#admin-content tbody tr').forEach(row => {
    row.hidden = !row.textContent.toLocaleLowerCase('vi').includes(query)
      || Boolean(status && row.dataset.status !== status);
  });
}

function tourManagement() {
  const rows = tours.map(t => {
    const status = t.hidden ? 'Đã ẩn' : 'Đang bán';
    return `<tr data-status="${status}"><td>${esc(t.title)}<br><small>${esc(t.province)} · ${status}</small></td>
      <td>${money(t.price)}</td><td>${t.departures.length}</td><td>
      <button onclick="editTour('${t.id}')">Sửa</button>
      <button class="outline" onclick="setTourVisibility('${t.id}',${!t.hidden})">${t.hidden ? 'Hiện lại' : 'Ẩn'}</button>
      </td></tr>`;
  });
  return `<div class="section-head"><h2>Quản lý tour</h2><button onclick="editTour()">+ Thêm tour</button></div>
    ${adminFilters('Tìm tên tour hoặc tỉnh', ['Đang bán', 'Đã ẩn'])}
    <div class="table-scroll"><table><thead><tr><th>Tour</th><th>Giá / khách</th><th>Đợt</th><th>Thao tác</th></tr></thead>
    <tbody>${rows.join('')}</tbody></table></div>`;
}

function editTour(id) {
  const t = tours.find(tour => tour.id === id);
  modal(`<h2>${t ? 'Sửa tour' : 'Thêm tour'}</h2>
    <form class="form" onsubmit="submitTour(event,'${t?.id || ''}')">
      <label>Tên tour<input name="title" required maxlength="120" value="${esc(t?.title)}"></label>
      <label>Tỉnh thành<select name="province">${PROVINCES.map(p =>
        `<option ${t?.province === p.name ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></label>
      <label>Giá mỗi khách<input name="price" type="number" min="1" max="1000000000" value="${t?.price || 2000000}" required></label>
      <label>Số ngày<input name="days" type="number" min="1" max="30" value="${t?.days || 3}" oninput="renderItinerary(this.value)" required></label>
      <label>Mô tả<textarea name="desc" required maxlength="4000">${esc(t?.desc)}</textarea></label>
      <label>Loại hình<select name="category">${['Biển đảo','Núi & thiên nhiên','Văn hóa & khám phá'].map(c =>
        `<option ${tourType(t || {}) === c ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
      <label>Ảnh tour (tối đa 1 MB)<input type="file" id="cover-upload" accept="image/jpeg,image/png,image/webp"></label>
      <label>Nguồn ảnh<input name="coverSource" value="${esc(t?.coverSource)}"></label>
      <label>Điểm đón<input name="pickup" value="${esc(t?.pickup)}"></label>
      <label>Bao gồm<textarea name="includes">${esc(t?.includes)}</textarea></label>
      <label>Không bao gồm<textarea name="excludes">${esc(t?.excludes)}</textarea></label>
      <fieldset><legend>Lịch trình từng ngày</legend><div id="itinerary-editor"></div></fieldset>
      <button type="submit">Lưu tour</button>
    </form>`);
  renderItinerary(t?.days || 3, t?.itinerary);
}

function renderItinerary(count, saved) {
  const values = saved || Array.from(document.querySelectorAll('[data-day]'), field => field.value);
  $('#itinerary-editor').innerHTML = Array.from({ length: Math.min(30, Math.max(0, Number(count))) },
    (_, i) => `<label>Ngày ${i + 1}<textarea data-day required maxlength="2000">${esc(values[i] ??
      'Tham quan, nghỉ ngơi và trải nghiệm địa phương.')}</textarea></label>`).join('');
}

async function submitTour(event, id) {
  event.preventDefault();
  const form = event.currentTarget;
  const fields = Object.fromEntries(new FormData(form));
  const existing = tours.find(t => t.id === id);
  const file = $('#cover-upload').files[0];
  const button = form.querySelector('[type=submit]');
  button.disabled = true;
  try {
    let cover = existing?.cover;
    if (file) {
      if (file.size > 1024 * 1024 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        throw new Error('Chọn ảnh JPG, PNG hoặc WebP tối đa 1 MB.');
      }
      cover = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Không đọc được ảnh.'));
        reader.readAsDataURL(file);
      });
    }
    fields.price = Number(fields.price);
    fields.days = Number(fields.days);
    fields.place = existing?.province === fields.province ? existing.place : province(fields.province).attractions[0];
    fields.itinerary = Array.from(form.querySelectorAll('[data-day]'), field => field.value);
    await operationsApi(id ? 'tours/' + id : 'tours', { ...fields, cover });
    $('#modal').close();
    await reloadAdmin('Đã lưu tour.');
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
}

async function setTourVisibility(id, hidden) {
  if (!confirm(hidden ? 'Ẩn tour này khỏi danh sách khách hàng?' : 'Hiện lại tour này?')) return;
  try {
    await operationsApi('tours/' + id + '/visibility', { hidden });
    await reloadAdmin('Đã cập nhật tour.');
  } catch (error) {
    toast(error.message);
  }
}

async function reloadAdmin(message) {
  await refreshOperations({ includeBookings: true });
  if (location.hash.startsWith('#admin')) showAdminTab(adminTab);
  toast(message);
}

function departureManagement() {
  return `<h2>Lịch khởi hành</h2><label>Chọn tour
    <select id="schedule-tour" onchange="showDepartureRows(this.value)">
      <option value="">Chọn tour</option>${tours.map(t => `<option value="${t.id}">${esc(t.title)}</option>`).join('')}
    </select></label><div id="departure-rows"></div>`;
}

function showDepartureRows(id) {
  const tour = tours.find(t => t.id === id);
  const container = $('#departure-rows');
  container.innerHTML = '';
  if (!tour) return;
  container.innerHTML = `<form class="form" onsubmit="submitDeparture(event,'${id}')">
    <div class="toolbar">
      <label>Ngày khởi hành<input type="date" name="day" required></label>
      <label>Sức chứa<input type="number" name="capacity" min="1" max="100" value="24" required></label>
      <button type="submit">Lưu đợt</button>
    </div>
    </form><div class="table-scroll"><table><thead><tr><th>Ngày đi</th><th>Sức chứa</th><th>Còn trống</th><th>Thao tác</th></tr></thead>
    <tbody>${tour.departures.map(d => `<tr><td>${date(d.day)}</td><td>${d.capacity}</td><td>${d.remaining}</td>
      <td><button class="outline" onclick="editDeparture('${d.day}', ${d.capacity})">Sửa</button>
      <button class="outline" onclick="removeDeparture('${id}','${d.day}')">Xóa</button></td></tr>`).join('')}</tbody></table></div>`;
}

function editDeparture(day, capacity) {
  const form = $('#departure-rows form');
  form.elements.day.value = day;
  form.elements.capacity.value = capacity;
  form.elements.capacity.focus();
}

async function submitDeparture(event, id) {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('[type=submit]');
  submit.disabled = true;
  try {
    await operationsApi('tours/' + id + '/departures', { day: form.elements.day.value, capacity: Number(form.elements.capacity.value) });
    await refreshSchedule(id);
    toast('Đã lưu đợt khởi hành.');
  } catch (error) {
    toast(error.message);
  } finally {
    submit.disabled = false;
  }
}

async function removeDeparture(id, day) {
  if (!confirm('Xóa đợt khởi hành này?')) return;
  try {
    await operationsApi('tours/' + id + '/remove-departure', { day });
    await refreshSchedule(id);
    toast('Đã xóa đợt khởi hành.');
  } catch (error) {
    toast(error.message);
  }
}

async function refreshSchedule(id) {
  await refreshOperations({ includeBookings: true });
  if (location.hash.startsWith('#admin') && adminTab === 'departures' && $('#schedule-tour')?.value === id) {
    showDepartureRows(id);
  }
}

function bookingManagement(payments) {
  const statusFor = b => payments ? (b.paid ? 'Đã thu tiền' : 'Chưa thu tiền') : statusName[b.status];
  const items = payments ? bookings.filter(b => b.status === 'confirmed') : bookings;
  const options = payments ? ['Đã thu tiền', 'Chưa thu tiền'] : Object.values(statusName);
  const rows = items.map(b => `<tr data-status="${statusFor(b)}">
    <td>${esc(b.id)}<br>${esc(b.name)}<br><small>${esc(b.phone)}</small></td>
    <td>${esc(b.title)}<br><small>${date(b.date)} · ${b.people} khách</small></td>
    <td>${money(b.total)}</td><td>${statusFor(b)}</td>
    <td><button class="outline" onclick="editBooking('${b.id}',${payments})">Mở phiếu</button></td></tr>`).join('');
  return `<h2>${payments ? 'Thu tiền và hoàn tiền' : 'Xử lý đơn đặt tour'}</h2>
    ${items.length ? `${adminFilters('Tìm tên khách, số điện thoại, mã đơn', options)}
    <div class="table-scroll"><table><thead><tr><th>Mã / khách</th><th>Chuyến đi</th><th>Tổng tiền</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
    <tbody>${rows}</tbody></table></div>` : '<p class="empty">Chưa có đơn để xử lý.</p>'}`;
}

function editBooking(id, payments) {
  const b = bookings.find(order => order.id === id);
  if (!b) return;
  const actions = payments ? [[b.paid ? 'refund' : 'collect', b.paid ? 'Ghi nhận hoàn tiền' : 'Ghi nhận đã thu']]
    : [...(b.status === 'pending' ? [['confirm', 'Xác nhận đơn']] : []),
       ...(b.status !== 'cancelled' && !b.paid ? [['cancel', 'Hủy và trả chỗ']] : [])];
  modal(`<h2>${payments ? 'Phiếu thanh toán' : 'Phiếu xử lý đơn'}</h2>
    <p>${esc(b.id)} · ${esc(b.title)}</p><p>${esc(b.name)} · ${date(b.date)} · ${b.people} khách</p>
    <p>${statusName[b.status]} · <strong>${money(b.total)}</strong></p>
    <form class="form" onsubmit="submitBookingAction(event,'${b.id}')">
      ${actions.map(([value, label]) => `<button type="submit" value="${value}">${label}</button>`).join('')}
    </form>`);
}

async function submitBookingAction(event, id) {
  event.preventDefault();
  const button = event.submitter;
  if (!button) return;
  if (button.value === 'cancel' && !confirm('Hủy đơn và trả lại chỗ?')) return;
  button.disabled = true;
  try {
    await operationsApi('bookings/' + id + '/' + button.value, {});
    $('#modal').close();
    await reloadAdmin('Đã cập nhật đơn.');
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
}
function destinationEditor(id){const p=PROVINCES.find(p=>String(p.id)===id);if(!p){$('#destination-editor').innerHTML='';return}$('#destination-editor').innerHTML=['attractions','specialties'].map(k=>`<h3>${k==='attractions'?'Địa danh':'Đặc sản'}</h3>${p[k].map((n,i)=>`<div class="destination-row"><span>${esc(n)}</span><button onclick="editDestination(${p.id},'${k}',${i})">Sửa</button><button class="outline" onclick="deleteDestination(${p.id},'${k}',${i})">Xóa</button></div>`).join('')}<button class="outline" onclick="editDestination(${p.id},'${k}',-1)">+ Thêm</button>`).join('')}
function editDestination(id,k,i){const p=PROVINCES.find(p=>p.id===id),n=p[k][i]||'',m=IMAGE_MAP[n]||{};modal(`<h2>${i<0?'Thêm':'Sửa'} ${k==='attractions'?'địa danh':'đặc sản'}</h2><form class="form" onsubmit="saveDestination(event,${id},'${k}',${i})"><label>Tên<input name="name" required value="${esc(n)}"></label><label>Mô tả ngắn<textarea name="description" required>${esc(m.description||'')}</textarea></label><label>Địa chỉ ảnh HTTPS<input name="url" type="url" required value="${esc(m.url?.startsWith('/')?location.origin+m.url:m.url||'')}"></label><label>Nguồn ảnh<input name="source" required value="${esc(m.source||'')}"></label><button>Lưu</button></form>`)}
function saveDestination(e,id,k,i){e.preventDefault();const f=new FormData(e.target),p=PROVINCES.find(p=>p.id===id),name=f.get('name').trim(),url=f.get('url');if(!url.startsWith('https://'))return toast('Dùng địa chỉ ảnh HTTPS.');if(p[k].some((x,j)=>x===name&&j!==i))return toast('Tên đã có trong danh sách.');if(i<0)p[k].push(name);else p[k][i]=name;IMAGE_MAP[name]={url,source:f.get('source'),description:f.get('description')};saveDestinations();$('#modal').close();destinationEditor(String(id))}
function deleteDestination(id,k,i){const p=PROVINCES.find(p=>p.id===id);if(p[k].length<=1)return toast('Giữ ít nhất một mục cho mỗi danh sách.');if(!confirm('Xóa '+p[k][i]+' khỏi danh sách?'))return;p[k].splice(i,1);saveDestinations();destinationEditor(String(id))}
function saveDestinations(){localStorage.setItem('mingo-destinations',JSON.stringify({provinces:PROVINCES,images:IMAGE_MAP}))}
