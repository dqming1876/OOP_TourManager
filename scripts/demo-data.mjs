import { pbkdf2Sync, randomBytes } from 'node:crypto';

export const demoCustomerPassword = 'MingoDemo26!';
const customers = ['Nguyễn An', 'Trần Hải', 'Lê Ngọc Mai', 'Phạm Quỳnh',
  'Vũ Minh Châu', 'Bùi Gia Hưng', 'Đặng Thanh Trúc', 'Đỗ Hoàng Sơn'];
const tours = [
  { id: 'demo-hanoi', title: 'Hà Nội – Phố cổ và Hồ Gươm', province: 'Hà Nội', price: 1200000,
    stops: ['Hồ Hoàn Kiếm', 'Văn Miếu'], activities: ['Đi bộ quanh hồ và khám phá phố cổ', 'Tham quan Văn Miếu và làng nghề'] },
  { id: 'demo-hue', title: 'Huế – Di sản bên sông Hương', province: 'Thành phố Huế', price: 1800000,
    stops: ['Đại Nội Huế', 'Chùa Thiên Mụ'], activities: ['Tìm hiểu Đại Nội và ẩm thực Huế', 'Thăm chùa, đi thuyền dọc sông Hương'] },
  { id: 'demo-dalat', title: 'Đà Lạt – Đồi thông và hồ', province: 'Lâm Đồng', price: 2400000,
    stops: ['Hồ Xuân Hương', 'Hồ Tuyền Lâm'], activities: ['Dạo ven hồ, ghé chợ Đà Lạt', 'Đi bộ ven rừng và ngắm Hồ Tuyền Lâm'] },
];
const originalOrders = (singleGuestOutcome) => [
  [2, 0, 'paid'],
  [2, 0, 'pending'],
  [1, 0, singleGuestOutcome],
  [2, 0, 'confirmed'],
];
const historicalOrders = originalOrders('refunded');
const nextMonthOrders = originalOrders('paid');
const extraOrders = [
  [1, 0, 'pending'],
  [2, 1, 'paid'],
  [1, 1, 'confirmed'],
  [2, 0, 'cancelled'],
  [3, 1, 'paid'],
  [1, 0, 'refunded'],
  [2, 2, 'confirmed'],
  [1, 2, 'pending'],
  [4, 0, 'paid'],
  [2, 1, 'pending'],
];
function sql(value) {
  return typeof value === 'number' ? String(value) : "'" + value.replaceAll("'", "''") + "'";
}

export function demoSql(now = new Date()) {
  const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' }).format(now);
  const [year, month] = today.split('-').map(Number);
  const scheduleDay = (offset, day) => new Date(Date.UTC(year, month - 1 + offset, day)).toISOString().slice(0, 10);
  const queries = [];
  const insert = (table, columns, values, ignore = false) =>
    queries.push(`INSERT ${ignore ? 'OR IGNORE ' : ''}INTO ${table} (${columns}) VALUES (${values.map(sql).join(',')});`);
  const update = (id, clause) => queries.push(`UPDATE bookings SET ${clause} WHERE id = ${sql(id)};`);
  customers.forEach((name, index) => {
    const salt = randomBytes(16).toString('hex');
    const hash = pbkdf2Sync(demoCustomerPassword, salt, 100000, 32, 'sha256').toString('hex');
    insert('accounts','id,username,name,password_hash,salt,email', [
      'demo-c' + index, 'mingo_khach' + (index + 1), name, hash, salt, 'mingo-khach' + (index + 1) + '@example.invalid',
    ]);
  });
  tours.forEach((tour, tourIndex) => {
    insert('tours', 'id,price,content', [tour.id, tour.price, JSON.stringify({
      title: tour.title, province: tour.province, place: tour.stops[0], days: 2, desc: tour.activities.join('. '),
    })]);
    tour.stops.forEach((place, index) => {
      insert('destinations', 'province,name', [tour.province, place], true);
      queries.push(`INSERT INTO tour_stops (tour_id,day_number,destination_id,activity)
        SELECT ${sql(tour.id)},${index + 1},id,${sql(tour.activities[index])} FROM destinations
        WHERE province = ${sql(tour.province)} AND name = ${sql(place)};`);
    });
    const currentEventDay = scheduleDay(0, 3 + tourIndex);
    const bookedThisMonth = currentEventDay < today ? currentEventDay : today;
    const departures = [
      { day: scheduleDay(-2, 12 + tourIndex), eventDay: scheduleDay(-2, 5 + tourIndex), capacity: 8, orders: historicalOrders },
      { day: scheduleDay(-1, 12 + tourIndex), eventDay: scheduleDay(-1, 5 + tourIndex), capacity: 8, orders: historicalOrders },
      { day: scheduleDay(1, 12 + tourIndex), eventDay: scheduleDay(1, 5 + tourIndex), capacity: 8, orders: nextMonthOrders },
      { day: scheduleDay(-3, 22 + tourIndex), eventDay: scheduleDay(-3, 3 + tourIndex), capacity: 30, orders: extraOrders },
      { day: scheduleDay(0, 22 + tourIndex), eventDay: bookedThisMonth, capacity: 28, orders: extraOrders },
      { day: scheduleDay(2, 22 + tourIndex), eventDay: bookedThisMonth, capacity: 24, orders: extraOrders },
    ];
    departures.forEach(({ day, eventDay, capacity, orders }, period) => {
      insert('departures', 'tour_id,day,capacity', [tour.id, day, capacity]);
      orders.forEach(([adults, children, outcome], index) => {
        const id = 'MGDEMO' + tourIndex + period + index;
        const customer = (tourIndex + period + index) % customers.length;
        insert('bookings','id,user_id,tour_id,day,title,name,phone,adults,children,unit_price,created_at', [
          id, 'demo-c' + customer, tour.id, day, tour.title, customers[customer],
          '09000000' + String(customer).padStart(2,'0'), adults, children, tour.price, eventDay + ' 09:00:00',
        ]);
        if (outcome === 'paid' || outcome === 'refunded') {
          update(id, "status = 'confirmed', paid = 1");
          if (outcome === 'refunded') update(id, "paid = 0, status = 'cancelled'");
          queries.push(`UPDATE payment_events SET recorded_on = ${sql(eventDay)} WHERE booking_id = ${sql(id)};`);
        }
        if (outcome === 'confirmed') update(id, "status = 'confirmed'");
        if (outcome === 'cancelled') update(id, "status = 'cancelled'");
      });
    });
  });
  return queries.join('\n') + '\n';
}
