const adminTabs = {
  overview: "Tổng quan",
  tours: "Quản lý tour",
  departures: "Lịch khởi hành",
  bookings: "Xử lý đơn",
  payments: "Thu tiền / hoàn tiền",
  destinations: "Điểm đến",
  reports: "Báo cáo",
};

function admin() {
  const nav = Object.entries(adminTabs).map(
    ([id, label]) =>
      `<button class="${adminTab === id ? "active" : ""}" onclick="showAdminTab('${id}')">${label}</button>`,
  );
  return `<section class="wrap">
    <div class="eyebrow">MINGO / QUẢN TRỊ</div>
    <div class="section-head"><h1 style="font-size:40px">Quản lý hành trình</h1>
    <button class="outline" onclick="adminLogout()">Đăng xuất Admin</button></div>
    <div class="admin-shell"><aside class="admin-nav">${nav.join("")}</aside><div id="admin-content">${adminContent()}</div></div>
  </section>`;
}

const liveAdminTabs = new Set(["overview", "bookings", "payments"]);
let adminSyncTimer;
let adminSyncPending = false;
let adminRenderedContent = "";

function showAdminTab(tab, refresh = true) {
  adminTab = tab;
  $("#app").innerHTML = admin();
  const content = $("#admin-live-data");
  if (content) adminRenderedContent = adminLiveContent(tab);
  if (tab === "reports") loadReport();
  clearInterval(adminSyncTimer);
  if (!liveAdminTabs.has(tab)) return;
  adminSyncTimer = setInterval(() => {
    if (!location.hash.startsWith("#admin")) {
      clearInterval(adminSyncTimer);
      return;
    }
    syncAdmin();
  }, 15000);
  if (refresh) syncAdmin();
}

async function syncAdmin(manual = false) {
  const tab = adminTab;
  const content = $("#admin-live-data");
  if (
    adminSyncPending ||
    !liveAdminTabs.has(tab) ||
    !content ||
    document.hidden ||
    $("#modal")?.open ||
    !location.hash.startsWith("#admin")
  )
    return;
  adminSyncPending = true;
  const status = $("#admin-sync-status");
  if (manual) status.textContent = "Đang cập nhật…";
  try {
    if (
      !(await refreshOperations({ includeBookings: true })) ||
      !content.isConnected
    )
      return;
    const next = adminLiveContent(tab);
    if (adminRenderedContent !== next) {
      const nextContent = document.createElement("template");
      nextContent.innerHTML = next;
      const currentRows = content.querySelector("tbody");
      const nextRows = nextContent.content.querySelector("tbody");
      if (tab !== "overview" && currentRows && nextRows) {
        currentRows.replaceChildren(...nextRows.children);
        filterAdminRows();
      } else {
        content.replaceChildren(nextContent.content);
      }
      adminRenderedContent = next;
    }
    status.textContent =
      "Đã cập nhật lúc " + new Date().toLocaleTimeString("vi-VN");
  } catch {
    if (content.isConnected)
      status.textContent = "Chưa đồng bộ được. Thử tải lại dữ liệu.";
  } finally {
    adminSyncPending = false;
  }
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) syncAdmin();
});

function adminContent() {
  if (adminTab === "reports") return reportPanel();
  if (adminTab === "tours") return tourManagement();
  if (adminTab === "departures") return departureManagement();
  if (liveAdminTabs.has(adminTab))
    return `<div class="toolbar">
    <button type="button" class="outline" onclick="syncAdmin(true)">Tải lại dữ liệu</button>
    <small id="admin-sync-status" class="muted" role="status"></small>
    </div><div id="admin-live-data">${adminLiveContent(adminTab)}</div>`;
  if (adminTab === "destinations") {
    return `<h2>Quản lý địa danh và đặc sản</h2><p class="muted">Thay đổi được lưu dùng chung. Tải lại trang để xem cập nhật từ phiên khác.</p>
      <label>Chọn tỉnh<select id="edit-province" onchange="destinationEditor(this.value)">
        <option value="">Chọn tỉnh thành</option>
        ${PROVINCES.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("")}
      </select></label><div id="destination-editor"></div>`;
  }
  return "";
}

function adminLiveContent(tab) {
  if (tab !== "overview") return bookingManagement(tab === "payments");
  const today = todayInVietnam();
  const forSale = tours.flatMap((tour) => {
    if (tour.hidden) return [];
    const next = tour.departures.find(
      (item) => item.day >= today && item.remaining > 0,
    );
    return next ? [{ tour, next }] : [];
  });
  const activeOrders = bookings.filter(
    (b) => b.date >= today && ["pending", "confirmed"].includes(b.status),
  );
  const revenue = bookings
    .filter((b) => b.paid)
    .reduce((sum, b) => sum + b.total, 0);
  return `<h2>Tổng quan</h2><div class="metrics">
    <div class="metric"><small>Tour đang bán</small><b>${wholeNumber(forSale.length)}</b></div>
    <div class="metric"><small>Đơn chờ xác nhận</small><b>${wholeNumber(activeOrders.filter((b) => b.status === "pending").length)}</b></div>
    <div class="metric"><small>Tiền đã thu</small><b>${money(revenue)}</b></div>
  </div>
  <section class="detail-section">
    <div class="section-head"><h3>Đơn đang xử lý</h3><button class="outline" onclick="showAdminTab('bookings')">Xem tất cả đơn</button></div>
    ${
      activeOrders.length
        ? `<div class="table-scroll"><table><thead><tr><th>Mã đơn</th><th>Tour</th><th>Khởi hành</th><th>Trạng thái</th></tr></thead>
    <tbody>${activeOrders
      .slice(0, 5)
      .map(
        (
          b,
        ) => `<tr><td><button class="outline" onclick="editBooking('${esc(b.id)}',false)">${esc(b.id)}</button></td>
      <td>${esc(b.title)}</td><td>${date(b.date)}</td><td>${bookingStatusLabel(b, today)}</td></tr>`,
      )
      .join("")}</tbody></table></div>`
        : '<p class="muted">Chưa có đơn cho các chuyến sắp khởi hành.</p>'
    }
  </section>
  <section class="detail-section"><h3>Tour đang bán</h3>
    ${
      forSale.length
        ? `<div class="table-scroll"><table><thead><tr><th>Tour</th><th>Đợt gần nhất còn chỗ</th><th class="number">Chỗ còn</th><th class="number">Giá / khách</th></tr></thead>
    <tbody>${forSale
      .map(
        ({
          tour,
          next,
        }) => `<tr><td><a href="#tour/${encodeURIComponent(tour.id)}">${esc(tour.title)}</a></td>
      <td>${date(next.day)}</td><td class="number">${wholeNumber(next.remaining)}</td><td class="number">${money(tour.price)}</td></tr>`,
      )
      .join("")}</tbody></table></div>`
        : '<p class="muted">Chưa có tour mở bán còn chỗ.</p>'
    }
  </section>`;
}

function adminFilters(placeholder, options) {
  return `<div class="toolbar">
    <input id="admin-search" aria-label="Tìm kiếm" placeholder="${placeholder}" oninput="filterAdminRows()">
    <select id="admin-status" aria-label="Lọc trạng thái" onchange="filterAdminRows()">
      <option value="">Tất cả trạng thái</option>${options.map((s) => `<option>${s}</option>`).join("")}
    </select>
    <button type="button" class="outline" onclick="clearAdminFilters()">Xóa lọc</button>
  </div>`;
}

function clearAdminFilters() {
  $("#admin-search").value = "";
  $("#admin-status").value = "";
  filterAdminRows();
}

function filterAdminRows() {
  const query = $("#admin-search").value.trim().toLocaleLowerCase("vi");
  const status = $("#admin-status").value;
  document.querySelectorAll("#admin-content tbody tr").forEach((row) => {
    row.hidden =
      !row.textContent.toLocaleLowerCase("vi").includes(query) ||
      Boolean(status && row.dataset.status !== status);
  });
}

function tourManagement() {
  const rows = tours.map((t) => {
    const status = t.hidden ? "Đã ẩn" : "Đang bán";
    return `<tr data-status="${status}"><td>${esc(t.title)}<br><small>${esc(t.province)} · ${status}</small></td>
      <td class="number">${money(t.price)}</td><td class="number">${wholeNumber(t.departures.length)}</td><td>
      <button type="button" class="outline" aria-controls="tour-detail" aria-expanded="false" onclick="showTourDetail(this,'${t.id}')">Chi tiết</button>
      <button onclick="editTour('${t.id}')">Sửa</button>
      <button class="outline" onclick="setTourVisibility('${t.id}',${!t.hidden})">${t.hidden ? "Hiện lại" : "Ẩn"}</button>
      </td></tr>`;
  });
  return `<div class="section-head"><h2>Danh mục tour</h2><button onclick="editTour()">+ Thêm tour</button></div>
    ${adminFilters("Tìm tên tour hoặc tỉnh", ["Đang bán", "Đã ẩn"])}
    <div class="table-scroll"><table><thead><tr><th>Tour</th><th class="number">Giá / khách</th><th class="number">Đợt</th><th>Thao tác</th></tr></thead>
    <tbody>${rows.join("")}</tbody></table></div>
    <section class="catalog-detail" id="tour-detail" aria-labelledby="tour-detail-heading" hidden></section>`;
}

function showTourDetail(button, id) {
  const tour = tours.find((item) => item.id === id);
  if (!tour) return;
  const panel = $("#tour-detail");
  const wasExpanded = button.getAttribute("aria-expanded") === "true";
  document
    .querySelectorAll('[aria-controls="tour-detail"]')
    .forEach((control) => control.setAttribute("aria-expanded", "false"));
  panel.hidden = wasExpanded;
  if (wasExpanded) return;
  button.setAttribute("aria-expanded", "true");
  panel.innerHTML = `<h3 id="tour-detail-heading" tabindex="-1">${esc(tour.title)}</h3>
    <dl><dt>Điểm đến</dt><dd>${esc(tour.place)} · ${esc(tour.province)}</dd>
    <dt>Thời lượng</dt><dd>${wholeNumber(tour.days)} ngày</dd>
    <dt>Giá mỗi khách</dt><dd class="number">${money(tour.price)}</dd></dl>
    <p>${esc(tour.desc)}</p><button type="button" class="outline" onclick="editTour('${tour.id}')">Sửa tour</button>`;
  $("#tour-detail-heading").focus();
}

function editTour(id) {
  const t = tours.find((tour) => tour.id === id);
  modal(`<h2>${t ? "Sửa tour" : "Thêm tour"}</h2>
    <form id="frm001_dm_tour" class="form catalog-form" data-validated novalidate onsubmit="submitTour(event,'${t?.id || ""}')">
      <label>Tên tour<input name="title" required maxlength="120" value="${esc(t?.title)}"></label>
      <label>Tỉnh thành<select name="province" onchange="renderItinerary(this.form.elements.days.value)">${PROVINCES.map(
        (p) =>
          `<option ${t?.province === p.name ? "selected" : ""}>${esc(p.name)}</option>`,
      ).join("")}</select></label>
      <label>Giá mỗi khách<input name="price" type="number" min="1" max="1000000000" value="${t?.price || 2000000}" required></label>
      <label>Số ngày<input name="days" type="number" min="1" max="30" value="${t?.days || 3}" oninput="renderItinerary(this.value)" required></label>
      <label>Mô tả<textarea name="desc" required maxlength="4000">${esc(t?.desc)}</textarea></label>
      <label>Loại hình<select name="category">${[
        "Biển đảo",
        "Núi & thiên nhiên",
        "Văn hóa & khám phá",
      ]
        .map(
          (c) =>
            `<option ${tourType(t || {}) === c ? "selected" : ""}>${c}</option>`,
        )
        .join("")}</select></label>
      <label>Ảnh tour (tối đa 1 MB)<input type="file" id="cover-upload" name="cover" accept="image/jpeg,image/png,image/webp"></label>
      <label>Nguồn ảnh<input name="coverSource" maxlength="2000" value="${esc(t?.coverSource)}"></label>
      <label>Điểm đón<input name="pickup" maxlength="2000" value="${esc(t?.pickup)}"></label>
      <label>Bao gồm<textarea name="includes" maxlength="2000">${esc(t?.includes)}</textarea></label>
      <label>Không bao gồm<textarea name="excludes" maxlength="2000">${esc(t?.excludes)}</textarea></label>
      <fieldset><legend>Lịch trình từng ngày</legend><p id="stop-count" aria-live="polite"></p><div id="itinerary-editor"></div></fieldset>
      <p class="submission-error" role="alert"></p><button type="submit">Lưu tour</button>
    </form>`);
  renderItinerary(t?.days || 3, t?.itinerary, t?.stops);
}

function renderItinerary(count, saved, savedStops) {
  const values =
    saved ||
    Array.from(document.querySelectorAll("[data-day]"), (field) => field.value);
  const stops =
    savedStops ||
    Array.from(
      document.querySelectorAll("[data-stop]"),
      (field) => field.value,
    );
  const names = province($("#modal form").elements.province.value).attractions;
  const length = Math.min(30, Math.max(0, Number(count)));
  $("#stop-count").textContent = "Lịch trình gồm " + length + " ngày.";
  $("#itinerary-editor").innerHTML = Array.from({ length }, (_, i) => {
    const options = [
      ...new Set([...names, ...(savedStops && stops[i] ? [stops[i]] : [])]),
    ];
    return `<div class="itinerary-row"><label>Điểm ghé ngày ${i + 1}<select name="stop-${i}" data-stop required>${options
      .map(
        (place) =>
          `<option ${place === stops[i] ? "selected" : ""}>${esc(place)}</option>`,
      )
      .join("")}</select></label>
      <label>Hoạt động ngày ${i + 1}<textarea name="itinerary-${i}" data-day required maxlength="2000">${esc(
        values[i] ?? "Tham quan, nghỉ ngơi và trải nghiệm địa phương.",
      )}</textarea></label></div>`;
  }).join("");
}

async function submitTour(event, id) {
  event.preventDefault();
  const form = event.currentTarget;
  form.querySelector(".submission-error").textContent = "";
  if (!validateMingoForm(form)) return;
  const fields = Object.fromEntries(new FormData(form));
  const existing = tours.find((t) => t.id === id);
  const file = $("#cover-upload").files[0];
  const button = form.querySelector("[type=submit]");
  button.disabled = true;
  try {
    let cover = existing?.cover;
    if (file) {
      cover = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () =>
          reject({ message: "Không đọc được ảnh.", field: "cover" });
        reader.readAsDataURL(file);
      });
    }
    fields.price = Number(fields.price);
    fields.days = Number(fields.days);
    fields.place =
      existing?.province === fields.province
        ? existing.place
        : province(fields.province).attractions[0];
    delete fields.cover;
    fields.itinerary = Array.from(
      form.querySelectorAll("[data-day]"),
      (field) => {
        delete fields[field.name];
        return field.value;
      },
    );
    fields.stops = Array.from(form.querySelectorAll("[data-stop]"), (field) => {
      delete fields[field.name];
      return field.value;
    });
    await operationsApi(id ? "tours/" + id : "tours", { ...fields, cover });
    $("#modal").close();
    await reloadAdmin("Đã lưu tour.");
  } catch (error) {
    showSubmissionError(form, error);
  } finally {
    button.disabled = false;
  }
}

async function setTourVisibility(id, hidden) {
  if (
    !confirm(
      hidden ? "Ẩn tour này khỏi danh sách khách hàng?" : "Hiện lại tour này?",
    )
  )
    return;
  try {
    await operationsApi("tours/" + id + "/visibility", { hidden });
    await reloadAdmin("Đã cập nhật tour.");
  } catch (error) {
    toast(error.message);
  }
}

async function reloadAdmin(message) {
  await refreshOperations({ includeBookings: true });
  if (location.hash.startsWith("#admin")) showAdminTab(adminTab, false);
  toast(message);
}

function departureManagement() {
  return `<h2>Lịch khởi hành</h2><label>Chọn tour
    <select id="schedule-tour" onchange="showDepartureRows(this.value)">
      <option value="">Chọn tour</option>${tours.map((t) => `<option value="${t.id}">${esc(t.title)}</option>`).join("")}
    </select></label><div id="departure-rows"></div>`;
}

function showDepartureRows(id) {
  const tour = tours.find((t) => t.id === id);
  const container = $("#departure-rows");
  container.innerHTML = "";
  if (!tour) return;
  container.innerHTML = `<h3 id="departure-form-title">Lập đợt khởi hành</h3><form id="frm002_nv_lich_khoi_hanh" class="form operation-form" data-validated novalidate onsubmit="submitDeparture(event,'${id}')">
    <div class="toolbar">
      <label>Ngày khởi hành<input type="date" name="day" min="${todayInVietnam()}" required></label>
      <label>Sức chứa<input type="number" name="capacity" min="1" max="100" value="24" required></label>
      <button type="submit">Lưu đợt</button>
      <button type="button" class="outline" onclick="resetDepartureForm()" hidden>Hủy sửa</button>
    </div>
    <p class="submission-error" role="alert"></p></form><div class="table-scroll"><table><thead><tr><th>Ngày đi</th><th class="number">Sức chứa</th><th class="number">Còn trống</th><th>Thao tác</th></tr></thead>
    <tbody>${tour.departures
      .map(
        (
          d,
        ) => `<tr><td>${date(d.day)}</td><td class="number">${wholeNumber(d.capacity)}</td><td class="number">${wholeNumber(d.remaining)}</td>
      <td><button class="outline" onclick="editDeparture('${d.day}', ${d.capacity})">Sửa</button>
      <button class="outline" onclick="removeDeparture('${id}','${d.day}')">Xóa</button></td></tr>`,
      )
      .join("")}</tbody></table></div>`;
}

function editDeparture(day, capacity) {
  const form = $("#departure-rows form");
  resetDepartureForm();
  form.dataset.edit = "true";
  $("#departure-form-title").textContent = "Đổi sức chứa đợt " + date(day);
  form.querySelector("[type=submit]").textContent = "Lưu sức chứa";
  form.querySelector("[type=button]").hidden = false;
  form.elements.day.readOnly = true;
  form.elements.day.value = day;
  form.elements.capacity.value = capacity;
  form.elements.capacity.focus();
}

function resetDepartureForm() {
  const form = $("#departure-rows form");
  delete form.dataset.edit;
  form.reset();
  form.elements.day.readOnly = false;
  for (const field of [form.elements.day, form.elements.capacity])
    showFieldError(field);
  form.querySelector(".submission-error").textContent = "";
  $("#departure-form-title").textContent = "Lập đợt khởi hành";
  form.querySelector("[type=submit]").textContent = "Lưu đợt";
  form.querySelector("[type=button]").hidden = true;
}

async function submitDeparture(event, id) {
  event.preventDefault();
  const form = event.currentTarget;
  form.querySelector(".submission-error").textContent = "";
  const day = form.elements.day.value;
  const edit = form.dataset.edit === "true";
  const departures = tours.find((tour) => tour.id === id)?.departures || [];
  const duplicate =
    !edit && departures.some((departure) => departure.day === day);
  if (
    !validateMingoForm(
      form,
      duplicate
        ? { day: "Ngày này đã có đợt. Dùng nút Sửa trong danh sách." }
        : {},
    )
  )
    return;
  const submit = form.querySelector("[type=submit]");
  submit.disabled = true;
  try {
    await operationsApi("tours/" + id + "/departures", {
      day,
      capacity: Number(form.elements.capacity.value),
      edit,
    });
    await refreshSchedule(id);
    toast("Đã lưu đợt khởi hành.");
  } catch (error) {
    showSubmissionError(form, error);
  } finally {
    submit.disabled = false;
  }
}

async function removeDeparture(id, day) {
  if (!confirm("Xóa đợt khởi hành này?")) return;
  try {
    await operationsApi("tours/" + id + "/remove-departure", { day });
    await refreshSchedule(id);
    toast("Đã xóa đợt khởi hành.");
  } catch (error) {
    toast(error.message);
  }
}

async function refreshSchedule(id) {
  await refreshOperations({ includeBookings: true });
  if (
    location.hash.startsWith("#admin") &&
    adminTab === "departures" &&
    $("#schedule-tour")?.value === id
  ) {
    showDepartureRows(id);
  }
}

function bookingManagement(payments) {
  const today = todayInVietnam();
  const statusFor = (b) =>
    payments
      ? b.paid
        ? "Đã thu tiền"
        : "Chưa thu tiền"
      : bookingStatusLabel(b, today);
  const items = payments
    ? bookings.filter((b) => b.status === "confirmed")
    : bookings;
  const options = payments
    ? ["Đã thu tiền", "Chưa thu tiền"]
    : [...Object.values(statusName), "Quá hạn xác nhận"];
  const rows = items
    .map(
      (b) => `<tr data-status="${statusFor(b)}">
    <td>${esc(b.id)}<br>${esc(b.name)}<br><small>${esc(b.phone)}</small></td>
    <td>${esc(b.title)}<br><small>${date(b.date)} · ${b.people} khách</small></td>
    <td class="number">${money(b.total)}</td><td>${statusFor(b)}</td>
    <td><button class="outline" onclick="editBooking('${b.id}',${payments})">Mở phiếu</button></td></tr>`,
    )
    .join("");
  return `<h2>${payments ? "Thu tiền và hoàn tiền" : "Xử lý đơn đặt tour"}</h2>
    ${
      items.length
        ? `${adminFilters("Tìm tên khách, số điện thoại, mã đơn", options)}
    <div class="table-scroll"><table><thead><tr><th>Mã / khách</th><th>Chuyến đi</th><th class="number">Tổng tiền</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`
        : '<p class="empty">Chưa có đơn để xử lý.</p>'
    }`;
}

async function editBooking(id, payments) {
  const b = bookings.find((order) => order.id === id);
  if (!b) return;
  let history;
  try {
    const result = await operationsApi("bookings/" + b.id + "/payments");
    history = result.payments;
  } catch (error) {
    toast(error.message);
    return;
  }
  if (!location.hash.startsWith("#admin")) return;
  // Older Worker versions did not include signedAmount in the payment payload.
  const net = history.reduce(
    (total, row) =>
      total +
      (row.signedAmount ?? (row.kind === "collect" ? row.amount : -row.amount)),
    0,
  );
  const today = todayInVietnam();
  const expired = b.status === "pending" && b.date < today;
  const actions = payments
    ? [
        [
          b.paid ? "refund" : "collect",
          b.paid ? "Ghi nhận hoàn tiền" : "Ghi nhận đã thu",
        ],
      ]
    : [
        ...(b.status === "pending" && !expired
          ? [["confirm", "Xác nhận đơn"]]
          : []),
        ...(b.status !== "cancelled" && !b.paid
          ? [["cancel", "Hủy và trả chỗ"]]
          : []),
      ];
  modal(`<h2>${payments ? "Phiếu thanh toán" : "Phiếu xử lý đơn"}</h2>
    <p>${esc(b.id)} · ${esc(b.title)}</p><p>${esc(b.name)} · ${date(b.date)} · ${b.people} khách</p>
    <p>${bookingStatusLabel(b, today)} · <strong>${money(b.total)}</strong></p>
    <p>${b.adults} người lớn · ${b.children} trẻ em · ${money(b.unitPrice)}/khách</p>
    <h3>Lịch sử thu và hoàn</h3>
    ${
      history.length
        ? `<table><thead><tr><th>Ngày ghi nhận</th><th>Thao tác</th><th>Số tiền</th></tr></thead>
    <tbody>${history
      .map(
        (
          row,
        ) => `<tr><td>${date(row.date)}</td><td>${row.kind === "collect" ? "Thu tiền" : "Hoàn tiền"}</td>
      <td class="report-number">${money(row.amount)}</td></tr>`,
      )
      .join("")}</tbody></table>`
        : "<p>Chưa có giao dịch.</p>"
    }
    <p>Đã thu ròng <b>${money(net)}</b> · Còn phải thu <b>${money(b.status === "cancelled" ? 0 : b.total - net)}</b></p>
    ${expired ? '<p class="notice">Đợt đã qua ngày khởi hành. Có thể hủy phiếu và trả chỗ.</p>' : ""}
    <form id="${payments ? "frm005_nv_thanh_toan" : "frm004_nv_xu_ly_don"}" class="form operation-form" onsubmit="submitBookingAction(event,'${b.id}')">
      ${actions.map(([value, label]) => `<button type="submit" value="${value}">${label}</button>`).join("")}
      <p class="submission-error" role="alert"></p>
    </form>`);
}

async function submitBookingAction(event, id) {
  event.preventDefault();
  const form = event.currentTarget;
  form.querySelector(".submission-error").textContent = "";
  const button = event.submitter;
  if (!button) return;
  if (button.value === "cancel" && !confirm("Hủy đơn và trả lại chỗ?")) return;
  button.disabled = true;
  try {
    await operationsApi("bookings/" + id + "/" + button.value, {});
    $("#modal").close();
    await reloadAdmin("Đã cập nhật đơn.");
  } catch (error) {
    showSubmissionError(form, error);
  } finally {
    button.disabled = false;
  }
}
function destinationEditor(id) {
  const p = PROVINCES.find((p) => String(p.id) === id);
  if (!p) {
    $("#destination-editor").innerHTML = "";
    return;
  }
  $("#destination-editor").innerHTML = ["attractions", "specialties"]
    .map(
      (k) =>
        `<h3>${k === "attractions" ? "Địa danh" : "Đặc sản"}</h3>${p[k]
          .map(
            (
              n,
              i,
            ) => `<div class="destination-row"><span>${esc(n)}</span><button onclick="editDestination(${p.id},'${k}',${i})">Sửa</button>
          <button class="outline" onclick="deleteDestination(${p.id},'${k}',${i})">Xóa</button></div>`,
          )
          .join(
            "",
          )}<button class="outline" onclick="editDestination(${p.id},'${k}',-1)">+ Thêm</button>`,
    )
    .join("");
}
function editDestination(id, k, i) {
  const p = PROVINCES.find((p) => p.id === id),
    n = p[k][i] || "",
    m = destinationMetadata(n, id, k);
  const entry = destinationEntries.filter(
    (row) => row.province_id === id && row.kind === k,
  )[i];
  modal(
    `<h2>${i < 0 ? "Thêm" : "Sửa"} ${k === "attractions" ? "địa danh" : "đặc sản"}</h2>
      <form id="frm009_dm_diem_den" data-entry="${esc(entry?.id || "")}" data-version="${entry?.version || ""}" class="form" onsubmit="saveDestination(event,${id},'${k}',${i})">
        <label>Tên<input name="name" required value="${esc(n)}">
      </label>
      <label>Mô tả ngắn<textarea name="description" required>${esc(m.description || "")}</textarea>
      </label>
      <label>Địa chỉ ảnh HTTPS<input name="url" type="url" required value="${esc(m.url?.startsWith("/") ? location.origin + m.url : m.url || "")}">
      </label>
      <label>Nguồn ảnh<input name="source" required value="${esc(m.source || "")}"></label><button>Lưu</button></form>`,
  );
}
async function saveDestination(e, id, kind, index) {
  e.preventDefault();
  const form = e.currentTarget;
  const button = form.querySelector("button");
  const data = Object.fromEntries(new FormData(form));
  const entry = form.dataset.entry
    ? { id: form.dataset.entry, version: Number(form.dataset.version) }
    : null;
  if (index >= 0 && !entry) return toast("Hãy tải lại danh mục trước khi sửa.");
  button.disabled = true;
  try {
    await operationsApi("destinations" + (entry ? "/" + entry.id : ""), {
      ...data,
      province_id: id,
      kind,
      version: entry?.version,
    });
    await refreshDestinations();
    $("#modal").close();
    destinationEditor(String(id));
    toast("Đã lưu danh mục dùng chung.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
}
async function deleteDestination(id, kind, index) {
  const entry = destinationEntries.filter(
    (row) => row.province_id === id && row.kind === kind,
  )[index];
  if (!entry) return toast("Hãy tải lại danh mục trước khi xóa.");
  if (!confirm("Xóa " + entry.name + " khỏi danh sách?")) return;
  try {
    await operationsApi("destinations/" + entry.id + "/remove", {
      version: entry.version,
    });
    await refreshDestinations();
    destinationEditor(String(id));
  } catch (error) {
    toast(error.message);
  }
}
