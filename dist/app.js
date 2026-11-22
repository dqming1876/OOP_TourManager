let adminLoaded = false,
  adminScriptPromise = null;
const $ = (s) => document.querySelector(s),
  esc = (s) =>
    String(s ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    ),
  money = (n) => wholeNumber(n) + " ₫";
let tours = [],
  bookings = [],
  user = null,
  adminTab = "overview";
function toast(s) {
  $("#toast").textContent = s;
  $("#toast").style.display = "block";
  setTimeout(() => ($("#toast").style.display = "none"), 3500);
}
function province(name) {
  return PROVINCES.find((p) => p.name === name) || PROVINCES[0];
}
function image(name, cls = "", metadata = null) {
  let m = metadata || window.IMAGE_MAP?.[name];
  return m
    ? `<img class="${cls}" src="${esc(m.url)}" alt="${esc(name)}" loading="lazy"><small class="source">Nguồn ảnh: ${esc(m.source)}</small>`
    : `<div class="placeholder">${esc(name)} · Đang bổ sung ảnh</div>`;
}
function photo(name) {
  const cover = tours.find((t) => t.place === name && t.cover)?.cover;
  if (cover)
    return `<img src="${esc(cover)}" alt="${esc(name)}" loading="lazy">`;
  let m = window.IMAGE_MAP?.[name];
  return m
    ? `<img src="${esc(m.url)}" alt="${esc(name)}" loading="lazy">`
    : `<div class="placeholder">${esc(name)}</div>`;
}
function card(t) {
  const p = province(t.province),
    departure = t.dates[0],
    seats = remaining(t, departure);
  return `<article class="tour-card" onmouseenter="positionTourPreview(this)" onfocusin="positionTourPreview(this)">
    <a href="#tour/${esc(t.id)}" class="tour">
      <div class="photo">${photo(t.place)}<span class="badge">${t.days} NGÀY ${t.days - 1} ĐÊM</span>
      </div>
      <small class="source">${IMAGE_MAP?.[t.place] ? "Nguồn ảnh: " + esc(IMAGE_MAP[t.place].source) : "Đang bổ sung ảnh"}</small>
      <p class="tour-type">${esc(tourType(t))}</p>
      <p class="sub">${esc(t.province)}</p>
      <h3>${esc(t.title)}</h3>
      <small>${t.dates.length} ngày khởi hành · Còn ${Math.max(0, seats)} chỗ</small>
    <div class="bottom">
    <div>
    <small>Từ </small>
    <span class="price">${money(t.bookingPrice ?? t.price)}</span>
    <small> / khách</small>
    </div>
    <span class="arrow">→</span>
    </div>
    <div class="tour-preview" id="preview-${esc(t.id)}">
    <span class="preview-kicker">XEM NHANH HÀNH TRÌNH</span>
    <dl>
    <div>
    <dt>Ghé thăm</dt>
    <dd>${esc(t.place)}</dd></div><div><dt>Hương vị địa phương</dt><dd>${esc(p.specialties.slice(0, 2).join(" · "))}</dd>
    </div>
    <div class="preview-schedule">
    <div>
    <dt>Khởi hành</dt>
    <dd>${date(departure)}</dd></div><div><dt>Chỗ còn lại</dt><dd>${Math.max(0, seats)} khách</dd>
    </div>
    </div>
    </dl>
    <span class="preview-action">Xem lịch trình chi tiết &nbsp; →</span>
    </div>
    </a>
    <button type="button" class="tour-preview-toggle" aria-label="Xem nhanh ${esc(t.title)}" aria-controls="preview-${esc(t.id)}" aria-expanded="false" onclick="toggleTourPreview(this)">Xem nhanh</button>
    </article>`;
}

function toggleTourPreview(button) {
  const card = button.closest(".tour-card");
  positionTourPreview(card);
  const open = card.classList.toggle("is-preview");
  positionTourPreview(card);
  button.setAttribute("aria-expanded", String(open));
  button.textContent = open ? "Đóng" : "Xem nhanh";
}

function date(d) {
  return d?.split("-").reverse().join("/") || "Chưa có lịch";
}
function options() {
  return ["Miền Bắc", "Miền Trung", "Miền Nam"]
    .map((name) => `<option value="${name}">${name}</option>`)
    .join("");
}
function priceOptions() {
  return (
    '<option value="0">Tất cả mức giá</option>' +
    [1, 2, 3, 4]
      .map(
        (n) =>
          `<option value="${n}">${wholeNumber(n * 1000000)} – ${wholeNumber((n + 1) * 1000000 - 1)} VND</option>`,
      )
      .join("") +
    '<option value="5">Trên 5.000.000 VND</option>'
  );
}
function matchesPrice(price, band) {
  return (
    !band ||
    (band === 5
      ? price >= 5000000
      : price >= band * 1000000 && price < (band + 1) * 1000000)
  );
}

function home() {
  return `<section class="hero">
    <div class="hero-copy">
    <div class="eyebrow">VIỆT NAM, THEO CÁCH CỦA BẠN</div>
    <h1>Đi để hiểu.<br>Đến để thương.</h1>
    <p>Từ miền núi đón mây đến những con phố bên sông. Chọn một nơi, dành vài ngày và mang về một câu chuyện.</p>
    <a href="#tours">
    <button>Tìm chuyến đi của bạn &nbsp; →</button>
    </a>
    </div>
    <div class="hero-photo">
    <img src="/images/trang-an-hero-hd.jpg" alt="Tràng An, Ninh Bình" fetchpriority="high" decoding="async">
    <div class="hero-tag">20°15′B · 105°55′Đ<b>Một chiều ở Tràng An</b>Ninh Bình, Việt Nam</div>
    <small class="source">Nguồn ảnh: Wikimedia Commons</small>
    </div>
    </section>
    <form class="searchbar" onsubmit="searchHome(event)">
    <label>Bạn muốn đi miền nào?<select id="home-province">
    <option value="">Tất cả</option>${options()}</select>
    </label>
    <label>Khoảng giá<select id="home-price">${priceOptions()}</select>
    </label>
    <label>Thời gian<select id="home-days">
    <option value="0">Mọi thời lượng</option>
    <option value="2">2 ngày</option>
    <option value="3">3 ngày</option>
    <option value="4">4 ngày</option>
    </select>
    </label>
    <button>Tìm tour →</button>
    </form>
    <section class="wrap">
    <div class="section-head">
    <div>
    <div class="eyebrow">GỢI Ý CHO CHUYẾN ĐI TỚI</div>
    <h2>Những hành trình đáng đi</h2>
    </div>
    <a class="textlink" href="#tours">Xem tất cả tour →</a>
    </div>
    <div class="grid">${tours
      .filter((t) => !t.hidden)
      .slice(0, 6)
      .map(card)
      .join("")}</div>
      </section>
      <section class="editorial">
      <div>
      <div class="eyebrow">ĐI MỘT NƠI, NHỚ MỘT VỊ</div>
      <h2>Có những miền đất<br>được nhớ bằng món ăn.</h2>
      <p>Một bát cao lầu giữa phố Hội, một món bánh nóng trong buổi sáng se lạnh. Mỗi chuyến đi đều có những hương vị để bạn tìm hiểu.</p>
      <a class="textlink" href="#places">Khám phá địa danh & đặc sản →</a>
      </div>
      <div class="photos">
      <figure>${image("Cao lầu Hội An")}<figcaption>Cao lầu · Hội An</figcaption>
      </figure>
      <figure>${image("Phố cổ Hội An")}<figcaption>Một góc phố Hội · Đà Nẵng</figcaption>
      </figure>
      </div>
      </section>
      <section class="wrap">
      <div class="section-head">
      <div>
      <div class="eyebrow">BẢN ĐỒ CHUYẾN ĐI</div>
      <h2>34 tỉnh thành. Vô vàn câu chuyện.</h2>
      </div>
      <a class="textlink" href="#places">Chọn điểm đến →</a>
      </div>
      <div class="province-grid">${PROVINCES.slice(0, 12).map(provinceCard).join("")}</div></section>`;
}
function provinceCard(p) {
  const code = p.plateLabel.match(/^\d+/)?.[0] || "";
  return `<a class="province" href="#province/${p.id}">
    <span class="province-name">${esc(p.name)}<small class="province-count">${tours.filter((t) => !t.hidden && t.province === p.name).length} tour</small>
    </span>
    <span class="province-code" aria-label="Biển số xe: ${esc(code)}">${esc(code)}</span></a>`;
}
function searchHome(e) {
  e.preventDefault();
  location.hash =
    "tours?region=" +
    encodeURIComponent($("#home-province").value) +
    "&price=" +
    $("#home-price").value +
    "&days=" +
    $("#home-days").value;
}
function catalog() {
  return `<section id="frm010_dm_tra_cuu_tour" class="wrap">
    <div class="eyebrow">CHỌN MỘT CHUYẾN ĐI</div>
    <h1 style="font-size:48px">Đi đâu tiếp theo?</h1>
    <p class="muted">34 hành trình mẫu cho 34 tỉnh, thành. Chọn nơi bạn muốn đến để khám phá.</p>
    <div class="toolbar">
    <input id="q" placeholder="Tìm tên tour, điểm đến…" aria-label="Tìm tour" oninput="filterTours()">
    <select id="p" aria-label="Miền" onchange="filterTours()">
    <option value="">Tất cả</option>${options()}</select>
    <select id="price" aria-label="Giá" onchange="filterTours()">${priceOptions()}</select>
    <select id="days" aria-label="Số ngày" onchange="filterTours()">
    <option value="0">Mọi thời lượng</option>
    <option value="2">2 ngày</option>
    <option value="3">3 ngày</option>
    <option value="4">4 ngày</option>
    </select>
    </div>
    <div class="toolbar">
    <label>Khởi hành từ<input type="date" id="from-date" onchange="filterTours()">
    </label>
    <label>Sắp xếp<select id="sort" onchange="filterTours()">
    <option value="default">Gợi ý</option>
    <option value="price">Giá tăng dần</option>
    <option value="price-desc">Giá giảm dần</option>
    <option value="days">Thời lượng ngắn nhất</option>
    <option value="date">Khởi hành sớm nhất</option>
    </select>
    </label>
    <button type="button" class="outline" onclick="resetTourFilters()">Xóa lọc</button>
    </div>
    <p id="count" class="muted">
    </p>
    <div id="results" class="grid">
    </div>
    </section>`;
}
let visibleTours = 12;

function resetTourFilters() {
  $("#q").value = "";
  $("#p").value = "";
  $("#price").value = "0";
  $("#days").value = "0";
  $("#from-date").value = "";
  $("#sort").value = "default";
  filterTours();
}

function filterTours(showMore = false) {
  visibleTours = showMore ? visibleTours + 12 : 12;
  const query = $("#q").value.trim().toLocaleLowerCase("vi");
  const region = $("#p").value;
  const price = Number($("#price").value);
  const days = Number($("#days").value);
  const from = $("#from-date").value;
  const sort = $("#sort").value;
  const firstDeparture = (tour) =>
    tour.dates.find((day) => day >= from) || "9999-12-31";
  const comparators = {
    price: (a, b) => (a.bookingPrice ?? a.price) - (b.bookingPrice ?? b.price),
    "price-desc": (a, b) =>
      (b.bookingPrice ?? b.price) - (a.bookingPrice ?? a.price),
    days: (a, b) => a.days - b.days,
    date: (a, b) => firstDeparture(a).localeCompare(firstDeparture(b)),
  };
  const matches = tours.filter(
    (tour) =>
      !tour.hidden &&
      (!region || province(tour.province).region === region) &&
      matchesPrice(tour.bookingPrice ?? tour.price, price) &&
      (!days || tour.days === days) &&
      (!from || tour.dates.some((day) => day >= from)) &&
      (tour.title + " " + tour.province)
        .toLocaleLowerCase("vi")
        .includes(query),
  );
  if (comparators[sort]) matches.sort(comparators[sort]);
  $("#count").textContent = wholeNumber(matches.length) + " hành trình phù hợp";
  $("#results").innerHTML = matches.length
    ? matches.slice(0, visibleTours).map(card).join("")
    : '<div class="empty" style="grid-column:1/-1">' +
      "<h3>Chưa có tour phù hợp</h3>" +
      "<p>Thử thay đổi bộ lọc hoặc khám phá Điểm đến.</p>" +
      '<a class="textlink" href="#places">Khám phá điểm đến →</a>' +
      "</div>";
  $("#more-tours")?.remove();
  if (matches.length > visibleTours) {
    const button = document.createElement("button");
    button.id = "more-tours";
    button.textContent = "Xem thêm hành trình";
    button.onclick = () => filterTours(true);
    $("#results").after(button);
  }
}
function places() {
  return `<section class="wrap">
    <div class="eyebrow">ĐỊA DANH & ẨM THỰC</div>
    <h1 style="font-size:48px">Việt Nam, từ Bắc vào Nam.</h1>
    <p class="muted">Danh mục Điểm đến theo địa giới sau sắp xếp năm 2025.</p>
    <div class="toolbar">
    <input id="place-q" placeholder="Tìm tỉnh thành…" oninput="filterPlaces()" aria-label="Tìm tỉnh thành">
    </div>
    <div id="province-list">${regionList(PROVINCES)}</div></section>`;
}
function filterPlaces() {
  let q = $("#place-q").value.toLowerCase();
  $("#province-list").innerHTML =
    regionList(PROVINCES.filter((p) => p.name.toLowerCase().includes(q))) ||
    "<p>Không tìm thấy tỉnh thành.</p>";
}
function destinationMetadata(name, provinceId, kind) {
  const entries = typeof destinationEntries === "undefined" ? [] : destinationEntries;
  return entries.find(row => row.name === name && row.province_id === provinceId && row.kind === kind)
    || IMAGE_MAP[name] || {};
}
function minis(list, provinceId, kind) {
  return `<div class="mini-grid">${list
    .map(
      (n) => `<article>${image(n, "", destinationMetadata(n, provinceId, kind))}<h3>${esc(n)}</h3>
    <p>${esc(destinationMetadata(n, provinceId, kind).description || "Gợi ý khám phá trong hành trình tại địa phương. Xem lịch trình tour để biết các điểm dừng được bao gồm.")}</p>
    </article>`,
    )
    .join("")}</div>`;
}
function provincePage(id) {
  let p = PROVINCES.find((p) => String(p.id) === String(id));
  if (!p) return '<div class="wrap">Không tìm thấy điểm đến.</div>';
  let ts = tours.filter((t) => t.province === p.name && !t.hidden);
  return `<section class="wrap">
    <div class="breadcrumb">
    <a href="#places">Điểm đến</a> / ${esc(p.name)}</div>
    <div class="eyebrow">MỘT ĐIỂM ĐẾN, NHIỀU TRẢI NGHIỆM</div>
    <h1>${esc(p.name)}</h1>
      <p class="muted">${esc(p.name)} thuộc ${esc(p.region)}, với những điểm dừng như ${esc(p.attractions.slice(0, 2).join(" và "))}. Khám phá cảnh sắc và thưởng thức ${esc(p.specialties[0])} trong chuyến đi của bạn.</p>
    <a class="textlink" href="#" onclick="event.preventDefault();document.getElementById('province-tours').scrollIntoView({behavior:'smooth'})">Xem tour tại ${esc(p.name)} →</a>
    <section class="detail-section">
    <h2>Những nơi nên ghé</h2>${minis(p.attractions, p.id, "attractions")}</section>
    <section class="detail-section">
    <h2>Đặc sản nên thử</h2>
    <p class="notice">Gợi ý thưởng thức, không mặc định bao gồm trong giá tour.</p>${minis(p.specialties, p.id, "specialties")}</section>
    <h2 id="province-tours" style="margin-bottom:25px">Tour đến ${esc(p.name)}</h2>
      <div class="grid">${ts.length ? ts.map(card).join("") : '<p class="muted">Lịch tour đang được xây dựng. Bạn có thể khám phá các địa danh và món ăn ở trên.</p>'}</div>
      </section>`;
}
function remaining(t, day) {
  return t.departures?.find((item) => item.day === day)?.remaining ?? 0;
}
function detail(id) {
  const t = tours.find((tour) => tour.id === id && !tour.hidden);
  if (!t)
    return '<div class="wrap">Tour đã ngừng bán hoặc không tồn tại.</div>';
  const p = province(t.province);
  return `<section class="wrap">
    <div class="breadcrumb">
    <a href="#tours">Lữ trình</a> / <a href="#province/${p.id}">${esc(t.province)}</a>
      </div>
      <div class="eyebrow">${t.days} NGÀY ${t.days - 1} ĐÊM · ${esc(t.province)}</div>
      <h1 class="detail-title">${esc(t.title)}</h1>
      <div class="detail-photo">${photo(t.place)}</div>
      <div class="tour-gallery">${p.attractions
        .filter((name) => IMAGE_MAP[name])
        .map(
          (n) =>
            `<button type="button" onclick="selectTourPhoto(this)">${photo(n)}</button>`,
        )
        .join(
          "",
        )}</div><small class="source">Nguồn ảnh: ${esc(IMAGE_MAP?.[t.place]?.source || "Đang bổ sung")}</small>
    <div class="tabs">
      <a href="#" onclick="event.preventDefault();$('#itinerary').scrollIntoView()">Lịch trình</a>
      <a href="#" onclick="event.preventDefault();$('#overview').scrollIntoView()">Tổng quan</a>
      <a href="#" onclick="event.preventDefault();$('#attractions').scrollIntoView()">Địa danh</a>
      <a href="#" onclick="event.preventDefault();$('#food').scrollIntoView()">Đặc sản</a>
      </div>
    <div class="detail-layout"><div>
    ${tourItinerary(t)}
    <section id="overview" class="detail-section">
      <h2>Một chuyến đi vừa vặn</h2>
      <p>${esc(t.desc)}</p>
      <p class="notice">Đón tại điểm hẹn trong tỉnh. Giá và lịch trình mẫu phục vụ đồ án, chưa bao gồm vé máy bay đến điểm đón. Các địa danh giới thiệu bên dưới không mặc định đều nằm trong lịch trình.</p>
      <p class="notice">Lịch trình và giá là dữ liệu mẫu phục vụ đồ án; chưa phải dịch vụ được mở bán thực tế.</p>
      <h3>Bao gồm</h3>
      <p>${esc(t.includes || "Di chuyển theo lịch trình, lưu trú và hướng dẫn viên tại điểm đến.")}</p>
        <h3>Không bao gồm</h3>
        <p>${esc(t.excludes || "Vé máy bay đến điểm đón, ăn uống tự túc và chi phí cá nhân.")}</p>
        <h3>Điểm đón</h3>
        <p>${esc(t.pickup || "Điểm hẹn tại trung tâm " + t.province + "; xác nhận địa chỉ cụ thể cùng nhân viên trước khi đặt.")}</p>
      <h3>Chính sách hủy</h3>
      <p>Đơn chờ xác nhận và chưa thanh toán có thể hủy tại Hành trình của tôi. Đơn đã xác nhận cần liên hệ quản trị viên; đơn đã thu tiền cần được ghi nhận hoàn tiền trước khi hủy.</p>
      </section>
      <section id="attractions" class="detail-section">
      <h2>Địa danh nổi bật tại điểm đến</h2>${minis(p.attractions, p.id, "attractions")}</section>
      <section id="food" class="detail-section">
      <h2>Hương vị của ${esc(t.province)}</h2>
      <p class="notice">Gợi ý thưởng thức · Chi phí ăn uống tự túc.</p>${minis(p.specialties, p.id, "specialties")}</section>
      </div>
    <aside class="booking-panel"><div class="eyebrow">ĐẶT CHUYẾN ĐI</div><span class="price">${money(t.bookingPrice ?? t.price)}</span><small> / khách</small>${t.bookingPrice && t.bookingPrice < t.price ? ` <small class="muted"><s>${money(t.price)}</s></small>` : ""}
    <form id="frm003_nv_dat_tour" data-price="${t.bookingPrice ?? t.price}" class="form operation-form" data-validated novalidate onsubmit="placeOrder(event,'${t.id}')"><label>Ngày khởi hành<select id="departure" name="day" required onchange="quote('${t.id}')">${t.dates.length ? "" : '<option value="">Chưa có lịch còn chỗ</option>'}${t.dates.map((d) => `<option value="${d}">${date(d)} — ${remaining(t, d)} chỗ</option>`).join("")}</select></label>${guestStepper(id, "people", "adults", "Người lớn", 1, 100)}
      ${guestStepper(id, "children", "children", "Trẻ em", 0, 99)}
      <p class="notice">Giá trẻ em bằng giá người lớn trong bản trải nghiệm. Mỗi khách sử dụng một chỗ.</p>
        <label>Họ tên người đại diện<input name="name" required maxlength="80" value="${esc(user?.name || "")}" autocomplete="name">
        </label>
        <label>Số điện thoại<input name="phone" type="tel" value="${esc(user?.phone || "")}" required minlength="9" maxlength="16" data-phone autocomplete="tel">
        </label>
        <div class="total">
        <span>Tổng tiền</span>
        <b id="quote" class="number">${money(t.bookingPrice ?? t.price)}</b>
        </div>
        <p class="submission-error" role="alert">
        </p>
        <button type="submit" ${t.dates.length ? "" : "disabled"}>Đặt tour &nbsp; →</button>
        <p class="notice">Đơn chờ xác nhận sẽ giữ chỗ. Bạn có thể hủy trước khi Admin xác nhận.</p>
        </form>
        </aside>
        </div>
        <section class="detail-section">
        <h2>Hành trình bạn có thể thích</h2>
        <div class="grid">${tours
          .filter(
            (x) =>
              !x.hidden &&
              x.id !== id &&
              province(x.province).region === p.region,
          )
          .slice(0, 3)
          .map(card)
          .join("")}</div></section></section>`;
}
function tourItinerary(tour) {
  const content = tour.itinerary?.length
    ? tour.itinerary
    : Array.from({ length: tour.days }, (_, index) => {
        if (index === 0)
          return "Đón đoàn tại điểm hẹn trong tỉnh, nhận phòng và dạo khu vực trung tâm.";
        if (index === tour.days - 1)
          return "Ăn sáng, tự do mua đặc sản địa phương, trả phòng và kết thúc hành trình.";
        return (
          "Dành ngày tham quan " +
          tour.place +
          ", nghỉ ngơi và trải nghiệm ẩm thực địa phương."
        );
      });
  return `<section id="itinerary" class="detail-section"><h2>Lịch trình dự kiến</h2>
    ${content
      .map(
        (text, index) => `<div class="day">
      <strong>NGÀY ${index + 1}</strong>
      <p>${tour.stops?.[index] ? `<b>${esc(tour.stops[index])}</b> · ` : ""}${esc(text)}</p>
      </div>`,
      )
      .join("")}
  </section>`;
}

function guestStepper(tourId, id, field, label, min, max) {
  return `<div class="guest-field"><label for="${id}">${label}</label><div class="stepper">
    <button type="button" aria-label="Giảm ${label.toLowerCase()}" onclick="stepGuests('${id}',-1)">−</button>
    <input type="number" id="${id}" name="${field}" min="${min}" max="${max}" value="${min}" required oninput="quote('${esc(tourId)}')">
    <button type="button" aria-label="Tăng ${label.toLowerCase()}" onclick="stepGuests('${id}',1)">+</button>
  </div></div>`;
}

function selectTourPhoto(button) {
  const selected = button.querySelector("img");
  const main = $(".detail-photo img");
  if (main && selected) {
    main.src = selected.src;
    main.alt = selected.alt;
  }
}

function quote(id) {
  const tour = tours.find((item) => item.id === id);
  const guests = (+$("#people").value || 0) + (+$("#children").value || 0);
  const available = Math.max(0, remaining(tour, $("#departure").value));
  $("#quote").textContent = money((tour.bookingPrice ?? tour.price) * guests);
  $('.booking-panel form [type="submit"]').textContent =
    guests > available ? "Kiểm tra số chỗ →" : "Đặt tour →";
}

function account() {
  if (user) {
    if (user.role === "admin") {
      location.hash = "admin";
      return;
    }
    location.hash = "profile";
    return;
  }
  modal(authForm());
}
function authForm(register = false) {
  return `<h2>${register ? "Tạo tài khoản" : "Đăng nhập"}</h2>
    <form id="${register ? "frm008_dang_ky" : "frm000_dang_nhap"}" class="form" data-validated novalidate onsubmit="${register ? "registerAccount" : "login"}(event)">${
      register
        ? '<label>Họ tên<input name="name" autocomplete="name" maxlength="80" required>' +
          "</label>"
        : ""
    }<label>Tên đăng nhập<input name="username" autocomplete="username" required minlength="3" maxlength="32" pattern="[A-Za-z0-9_]+">
    </label>
    <label>Mật khẩu<input name="password" type="password" autocomplete="${register ? "new-password" : "current-password"}" required ${register ? 'minlength="6"' : ""} maxlength="128">
    </label>
    <p id="auth-error" class="submission-error" role="alert" style="color:var(--orange)">
    </p>
    <button type="submit">${register ? "Đăng ký" : "Đăng nhập"}</button>
    </form>
    <p style="text-align:center;margin-bottom:0">${register ? "Đã có tài khoản?" : "Chưa có tài khoản?"} <button class="auth-link" onclick="$('#modal-body').innerHTML=authForm(${!register})">${register ? "Đăng nhập" : "Đăng ký"}</button>
      </p>`;
}
async function authSubmit(e, path) {
  e.preventDefault();
  const form = e.target;
  $("#auth-error").textContent = "";
  if (!validateMingoForm(form)) return null;
  let button = form.querySelector("button[type=submit]");
  button.disabled = true;
  try {
    let r = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.fromEntries(new FormData(form))),
      }),
      data = await r.json();
    if (!r.ok) {
      $("#auth-error").textContent =
        data.error || "Không thể thực hiện. Vui lòng thử lại.";
      return null;
    }
    return data;
  } catch {
    $("#auth-error").textContent = "Không thể kết nối. Vui lòng thử lại.";
    return null;
  } finally {
    button.disabled = false;
  }
}
async function login(e) {
  let data = await authSubmit(e, "/api/auth/login");
  if (!data) return;
  user = data.user;
  $("#modal").close();
  if (user.role === "admin") {
    location.hash = "admin";
    render();
  } else {
    render();
    loadPublicOperations();
  }
  toast("Đăng nhập thành công.");
}
async function registerAccount(e) {
  let data = await authSubmit(e, "/api/auth/register");
  if (!data) return;
  $("#modal-body").innerHTML = authForm();
  toast("Đăng ký thành công. Bạn có thể đăng nhập ngay.");
}
async function logout() {
  try {
    let r = await fetch("/api/auth/logout", { method: "POST" });
    if (!r.ok) throw Error();
    user = null;
    bookings = [];
    location.hash = "home";
    render();
    toast("Đã đăng xuất.");
  } catch {
    toast("Chưa thể đăng xuất. Vui lòng thử lại.");
  }
}
function profilePage() {
  if (!user || user.role !== "customer")
    return (
      '<section class="wrap">' +
      "<h2>Thông tin cá nhân</h2>" +
      "<p>Vui lòng đăng nhập tài khoản khách hàng.</p>" +
      '<button onclick="account()">Đăng nhập</button>' +
      "</section>"
    );
  return `<section class="wrap" style="max-width:700px">
    <div class="eyebrow">TÀI KHOẢN CỦA BẠN</div>
    <div class="section-head">
    <h1 style="font-size:40px">Thông tin cá nhân</h1>
    <button class="outline" onclick="logout()">Đăng xuất</button>
    </div>
    <p class="muted">Tên đăng nhập: <b>${esc(user.username)}</b>
    </p>
    <form id="frm006_nv_ho_so" class="form operation-form" data-validated novalidate onsubmit="saveProfile(event)">
    <label>Họ tên<input name="name" value="${esc(user.name)}" maxlength="80" required autocomplete="name">
    </label>
    <label>Email (không bắt buộc)<input name="email" type="email" value="${esc(user.email)}" maxlength="120" autocomplete="email">
    </label>
    <label>Số điện thoại (không bắt buộc)<input name="phone" type="tel" value="${esc(user.phone)}" maxlength="20" data-phone autocomplete="tel">
    </label>
    <label>Ngày sinh (không bắt buộc)<input name="birthday" type="date" value="${esc(user.birthday)}">
    </label>
    <label>Địa chỉ (không bắt buộc)<textarea name="address" maxlength="250" autocomplete="street-address">${esc(user.address)}</textarea>
    </label>
    <p class="submission-error" role="alert">
    </p>
    <button>Lưu thông tin</button>
    </form>
    </section>`;
}
async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  form.querySelector(".submission-error").textContent = "";
  if (!validateMingoForm(form)) return;
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const response = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const data = await response.json();
    if (!response.ok) {
      showSubmissionError(form, { message: data.error, field: data.field });
      return;
    }
    user = data.user;
    render();
    toast("Đã lưu thông tin cá nhân.");
  } catch {
    showSubmissionError(
      form,
      new Error("Không thể kết nối. Vui lòng thử lại."),
    );
  } finally {
    button.disabled = false;
  }
}
async function restoreAccount() {
  try {
    let r = await fetch("/api/auth/me", { cache: "no-store" });
    if (r.ok) {
      user = (await r.json()).user;
      render();
      loadPublicOperations();
    }
  } catch {
    toast("Không thể kiểm tra phiên. Vui lòng tải lại trang.");
  }
}
function modal(html) {
  $("#modal-body").innerHTML = html;
  $("#modal").showModal();
}
const statusName = {
  pending: "Chờ xác nhận",
  confirmed: "Đã xác nhận",
  cancelled: "Đã hủy",
};
function bookingStatusLabel(booking, today = todayInVietnam()) {
  return booking.status === "pending" && booking.date < today
    ? "Quá hạn xác nhận"
    : statusName[booking.status];
}

function myBookings() {
  let a = user ? bookings.filter((b) => b.userId === user.id) : [];
  return `<section id="frm011_nv_don_cua_toi" class="wrap">
    <div class="eyebrow">CHUYẾN ĐI CỦA BẠN</div>
    <h1 style="font-size:48px">Những cuộc hẹn với Việt Nam</h1>
    <p class="muted">Theo dõi lịch khởi hành và trạng thái đặt tour.</p>${
      !user
        ? '<div class="empty">' +
          "<h3>Đăng nhập để xem đơn</h3>" +
          "<p>Dùng tài khoản đã đặt tour.</p>" +
          '<button onclick="account()">Đăng nhập</button>' +
          "</div>"
        : !a.length
          ? '<div class="empty">' +
            "<h3>Chuyến đi đầu tiên đang chờ bạn.</h3>" +
            "<p>Chọn một hành trình để bắt đầu.</p>" +
            '<a href="#tours">' +
            "<button>Tìm tour →</button>" +
            "</a>" +
            "</div>"
          : a
              .map(
                (b) => `<article class="booking-row">
    <div>
    <button class="outline" onclick="bookingDetail('${esc(b.id)}')">Chi tiết đơn</button>
      <small>${b.id} · ${date(b.date)}</small>
      <h3>${esc(b.title)}</h3>
      <span class="status ${b.status === "cancelled" ? "cancel" : ""}">${bookingStatusLabel(b)}</span>
      <p>${b.people} khách · ${b.paid ? "Đã thanh toán" : "Chưa thanh toán"}</p>
      </div>
      <div>
      <b>${money(b.total)}</b>
      <p>${esc(b.name)}</p>${b.status === "pending" ? `<button class="outline" onclick="performBookingAction('${b.id}','cancel')">Hủy đơn</button>` : ""}</div>
      </article>`,
              )
              .join("")
    }</section>`;
}
let tourObserver;

function observeTourSections() {
  tourObserver?.disconnect();
  const tabs = [...document.querySelectorAll(".tabs a")];
  const sections = [
    ...document.querySelectorAll(".detail-layout .detail-section[id]"),
  ];
  if (!sections.length) return;
  const activate = (active) =>
    tabs.forEach((tab) => tab.classList.toggle("active", tab === active));
  activate(tabs[0]);
  for (const tab of tabs) tab.addEventListener("click", () => activate(tab));
  tourObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting)
          activate(
            tabs.find((tab) =>
              tab
                .getAttribute("onclick")
                .includes("'#" + entry.target.id + "'"),
            ),
          );
      }
    },
    { rootMargin: "-140px 0px -55% 0px" },
  );
  for (const section of sections) tourObserver.observe(section);
}

function render() {
  const adminNav = $("#admin-nav");
  if (adminNav) adminNav.hidden = user?.role !== "admin";
  $("#account").textContent = user ? user.name + " →" : "Đăng nhập →";
  const [path, query] = (location.hash.slice(1) || "home").split("?");
  const [page, id] = path.split("/");
  const views = {
    home,
    tours: catalog,
    places,
    province: provincePage,
    tour: detail,
    bookings: myBookings,
    admin: adminLoading,
    profile: profilePage,
  };
  const view = Object.hasOwn(views, page) ? views[page] : home;
  $("#app").innerHTML = view(id);
  if (page === "tours") {
    const filters = new URLSearchParams(query);
    $("#p").value =
      filters.get("region") ||
      PROVINCES.find((p) => p.name === filters.get("province"))?.region ||
      "";
    $("#price").value = ["1", "2", "3", "4", "5"].includes(filters.get("price"))
      ? filters.get("price")
      : "0";
    $("#days").value = filters.get("days") || "0";
    filterTours();
  }
  if (page === "admin") openAdmin();
  observeTourSections();
  const title =
    page === "admin"
      ? "Quản trị"
      : page === "tour"
        ? tours.find((tour) => tour.id === id)?.title || "Tour"
        : "mingo — Đi để hiểu, đến để thương";
  document.title = title + " | mingo";
}

window.addEventListener("hashchange", () => {
  render();
  scrollTo(0, 0);
});

function adminLoading() {
  return '<section class="wrap"><p>Đang kiểm tra phiên quản trị…</p></section>';
}
function adminLoginPage(error = "") {
  return `<section class="wrap" style="max-width:520px">
    <div class="eyebrow">KHU VỰC QUẢN TRỊ</div>
    <h1 style="font-size:38px">Đăng nhập</h1>
    <p class="muted">Vui lòng đăng nhập bằng tài khoản quản trị.</p>
    <p role="alert">${esc(error)}</p>
    <button onclick="modal(authForm())">Đăng nhập</button>
    </section>`;
}
async function openAdmin() {
  try {
    let r = await fetch("/api/admin/session", { cache: "no-store" });
    if (!r.ok) throw Error("network");
    let a = await r.json();
    if (!location.hash.startsWith("#admin")) return;
    if (!a.authenticated) {
      $("#app").innerHTML = adminLoginPage();
      return;
    }
    if (!adminLoaded) {
      if (!adminScriptPromise)
        adminScriptPromise = new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = "/admin.js?v=review3";
          script.onload = resolve;
          script.onerror = () => {
            script.remove();
            adminScriptPromise = null;
            reject(new Error("Không tải được giao diện quản trị"));
          };
          document.head.appendChild(script);
        });
      await adminScriptPromise;
      adminLoaded = true;
    }
    if (!(await refreshOperations({ includeBookings: true }))) return;
    if (location.hash.startsWith("#admin")) showAdminTab(adminTab, false);
  } catch (e) {
    $("#app").innerHTML = adminLoginPage(
      "Không thể kiểm tra phiên quản trị. Vui lòng thử lại.",
    );
  }
}
async function adminLogout() {
  await logout();
}

function positionTourPreview(card) {
  const panel = card.querySelector(".tour-preview");
  if (!panel) return;
  const rect = card.getBoundingClientRect(),
    scale = matchMedia("(hover:hover) and (pointer:fine)").matches ? 1.1 : 1,
    width = card.offsetWidth,
    center = rect.left + rect.width / 2,
    left = center - (width * scale) / 2,
    right = center + (width * scale) / 2,
    spaceLeft = left - 20,
    spaceRight = innerWidth - right - 20,
    side = spaceRight >= 300 || spaceRight >= spaceLeft ? "right" : "left",
    space = Math.max(spaceLeft, spaceRight);
  card.dataset.previewSide = space < 220 ? "inside" : side;
  panel.style.setProperty(
    "--preview-width",
    Math.min(320, Math.max(220, space - 12)) / scale + "px",
  );
  const visualHeight = panel.offsetHeight * scale,
    top = Math.max(12, Math.min(rect.top, innerHeight - visualHeight - 16));
  panel.style.setProperty("--preview-y", (top - rect.top) / scale + "px");
}
window.addEventListener("resize", () => {
  document
    .querySelectorAll(
      ".tour-card:hover,.tour-card.is-preview,.tour-card:focus-within",
    )
    .forEach(positionTourPreview);
});

function regionList(list) {
  return ["Miền Bắc", "Miền Trung", "Miền Nam"]
    .map((r) => {
      const ps = list.filter((p) => p.region === r);
      return ps.length
        ? `<section class="region-block"><h2>${r}</h2><div class="province-grid">${ps.map(provinceCard).join("")}</div></section>`
        : "";
    })
    .join("");
}
function stepGuests(field, delta) {
  const input = document.getElementById(field);
  input.value = Math.max(
    +input.min,
    Math.min(+input.max, (+input.value || 0) + delta),
  );
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function tourType(t) {
  if (t.category) return t.category;
  return /biển|vịnh|đảo|phú quốc|cát bà|hạ long/i.test(t.title + " " + t.place)
    ? "Biển đảo"
    : /núi|đèo|sa pa|đà lạt|fansipan|bản |mây/i.test(t.title + " " + t.place)
      ? "Núi & thiên nhiên"
      : "Văn hóa & khám phá";
}
function bookingDetail(id) {
  const b = bookings.find(
    (b) => b.id === id && (user?.role === "admin" || b.userId === user?.id),
  );
  if (!b) return;
  modal(
    `<h2>Đơn ${esc(b.id)}</h2>
      <h3>${esc(b.title)}</h3>
      <p>Khởi hành: ${date(b.date)}</p>
      <p>${b.adults ?? b.people} người lớn · ${b.children || 0} trẻ em</p>
      <p>Liên hệ: ${esc(b.name)} · ${esc(b.phone)}</p>
      <p>${bookingStatusLabel(b)} · ${b.paid ? "Đã thanh toán" : "Chưa thanh toán"}</p>
      <p>Tổng tiền: <strong>${money(b.total)}</strong>
      </p>
      <a class="textlink" href="#tour/${esc(b.tourId)}" onclick="document.querySelector('dialog').close()">Xem tour →</a>`,
  );
}
function photoCredits() {
  const names = [
    ...new Set(Object.values(IMAGE_MAP).map((x) => x.source)),
  ].sort();
  modal(
    "<h2>Nguồn ảnh</h2><p>Ảnh địa danh, đặc sản trong website được tổng hợp từ các nguồn dưới đây.</p>" +
      names.map((n) => "<p>" + esc(n) + "</p>").join("") +
      "<p>Ảnh tour do quản trị viên tải lên: người tải lên cung cấp và chịu trách nhiệm ghi nguồn.</p>",
  );
}
const creditButton = document.createElement("button");
creditButton.className = "outline";
creditButton.textContent = "Nguồn ảnh";
creditButton.onclick = photoCredits;
document.querySelector("footer").append(creditButton);
render();
