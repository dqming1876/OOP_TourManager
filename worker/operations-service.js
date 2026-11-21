class OperationError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function requiredText(value, limit, label) {
  if (typeof value !== 'string' || !value.trim() || value.trim().length > limit) {
    throw new OperationError(400, label + ' không hợp lệ.');
  }
  return value.trim();
}

function integerBetween(value, min, max, label) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new OperationError(400, label + ' phải từ ' + min + ' đến ' + max + '.');
  }
  return value;
}

function departureDay(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)
    || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0, 10) !== value) {
    throw new OperationError(400, 'Ngày khởi hành không hợp lệ.');
  }
  return value;
}

class TourOperations {
  constructor(repository, actor, today) {
    this.repository = repository;
    this.actor = actor;
    this.today = today;
  }

  requireRole(role) {
    if (!this.actor) throw new OperationError(401, 'Vui lòng đăng nhập.');
    if (this.actor.role !== role) throw new OperationError(403, 'Bạn không có quyền thực hiện thao tác này.');
  }

  catalog() {
    return this.repository.catalog(this.actor?.role === 'admin');
  }

  bookings() {
    if (this.actor?.role === 'admin') return this.repository.listBookings(null);
    this.requireRole('customer');
    return this.repository.listBookings(this.actor.id);
  }

  async saveTour(id, input) {
    this.requireRole('admin');
    const tourId = id || crypto.randomUUID();
    const days = integerBetween(input.days, 1, 30, 'Số ngày');
    const tour = {
      title: requiredText(input.title, 120, 'Tên tour'),
      province: requiredText(input.province, 80, 'Tỉnh thành'),
      place: requiredText(input.place, 120, 'Điểm đến'),
      price: integerBetween(input.price, 1, 1_000_000_000, 'Giá tour'),
      desc: requiredText(input.desc, 4000, 'Mô tả'),
      days,
    };
    for (const field of ['category', 'pickup', 'includes', 'excludes', 'coverSource']) {
      if (input[field]) tour[field] = requiredText(input[field], 2000, field);
    }
    if (input.itinerary !== undefined) {
      if (!Array.isArray(input.itinerary) || input.itinerary.length !== days) {
        throw new OperationError(400, 'Lịch trình phải có đủ nội dung mỗi ngày.');
      }
      tour.itinerary = input.itinerary.map(day => requiredText(day, 2000, 'Nội dung lịch trình'));
      if (input.stops !== undefined && (!Array.isArray(input.stops) || input.stops.length !== days)) {
        throw new OperationError(400, 'Chọn điểm ghé cho từng ngày.');
      }
      tour.stops = input.stops?.map(place => requiredText(place, 120, 'Điểm ghé')) ?? tour.itinerary.map(() => tour.place);
    }
    if (input.cover) {
      if (typeof input.cover !== 'string' || input.cover.length > 1_398_134
        || !/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(input.cover)) {
        throw new OperationError(400, 'Ảnh phải là JPG, PNG hoặc WebP tối đa 1 MB.');
      }
      tour.cover = input.cover;
    }
    if (!await this.repository.saveTour(tourId, tour, !id)) throw new OperationError(404, 'Không tìm thấy tour.');
    return { id: tourId };
  }

  async setVisibility(id, hidden) {
    this.requireRole('admin');
    if (typeof hidden !== 'boolean') throw new OperationError(400, 'Trạng thái hiển thị không hợp lệ.');
    if (!await this.repository.setVisibility(id, hidden)) throw new OperationError(404, 'Không tìm thấy tour.');
  }

  async saveDeparture(tourId, input) {
    this.requireRole('admin');
    const day = departureDay(input.day);
    const capacity = integerBetween(input.capacity, 1, 100, 'Sức chứa');
    if (day < this.today) throw new OperationError(400, 'Không thể sửa lịch đã qua.');
    if (!await this.repository.saveDeparture(tourId, day, capacity)) {
      throw new OperationError(409, 'Tour không tồn tại hoặc sức chứa thấp hơn số chỗ đã giữ.');
    }
  }

  async placeBooking(input) {
    this.requireRole('customer');
    const booking = {
      tourId: requiredText(input.tourId, 70, 'Tour'),
      day: departureDay(input.day),
      name: requiredText(input.name, 80, 'Tên người đại diện'),
      phone: requiredText(input.phone, 16, 'Số điện thoại'),
      adults: integerBetween(input.adults, 1, 100, 'Số người lớn'),
      children: integerBetween(input.children, 0, 99, 'Số trẻ em'),
    };
    if (!/^[0-9+ ()-]{9,16}$/.test(booking.phone) || booking.phone.replace(/\D/g, '').length < 8) {
      throw new OperationError(400, 'Số điện thoại không hợp lệ.');
    }
    const id = 'MG' + crypto.randomUUID().replaceAll('-', '').toUpperCase();
    if (!await this.repository.placeBooking(id, this.actor.id, booking, this.today)) {
      throw new OperationError(409, 'Đợt khởi hành đã đóng hoặc không còn đủ chỗ.');
    }
    return { id };
  }

  async removeDeparture(tourId, value) {
    this.requireRole('admin');
    const day = departureDay(value);
    if (!await this.repository.removeDeparture(tourId, day)) {
      throw new OperationError(409, 'Đợt không tồn tại hoặc đã có lịch sử đặt chỗ.');
    }
  }

  async updateBooking(id, action) {
    if (!['confirm', 'collect', 'refund', 'cancel'].includes(action)) {
      throw new OperationError(400, 'Thao tác đơn không hợp lệ.');
    }
    const role = action === 'cancel' && this.actor?.role === 'customer' ? 'customer' : 'admin';
    this.requireRole(role);
    const ownerId = role === 'customer' ? this.actor.id : null;
    if (!await this.repository.updateBooking(id, action, ownerId)) {
      throw new OperationError(409, 'Không thể thao tác với đơn này ở trạng thái hiện tại.');
    }
  }
}
