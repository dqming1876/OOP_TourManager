import { AccessError, AppError, ConflictError, ValidationError } from '../domain/errors.js';
import { calendarDay, integerBetween, requiredText } from '../domain/validation.js';

function departureDay(value) {
  return calendarDay(value, 'Ngày khởi hành không hợp lệ.', 'day');
}

export class TourOperations {
  constructor(repository, actor, today) {
    this.repository = repository;
    this.actor = actor;
    this.today = today;
  }

  requireRole(role) {
    if (!this.actor) throw new AccessError(401, 'Vui lòng đăng nhập.');
    if (this.actor.role !== role) throw new AccessError(403, 'Bạn không có quyền thực hiện thao tác này.');
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
    const days = integerBetween(input.days, 1, 30, 'Số ngày', 'days');
    const tour = {
      title: requiredText(input.title, 120, 'Tên tour', 'title'),
      province: requiredText(input.province, 80, 'Tỉnh thành', 'province'),
      place: requiredText(input.place, 120, 'Điểm đến', 'place'),
      price: integerBetween(input.price, 1, 1_000_000_000, 'Giá tour', 'price'),
      desc: requiredText(input.desc, 4000, 'Mô tả', 'desc'),
      days,
    };
    for (const field of ['category', 'pickup', 'includes', 'excludes', 'coverSource']) {
      if (input[field]) tour[field] = requiredText(input[field], 2000, field, field);
    }
    if (input.itinerary !== undefined) {
      if (!Array.isArray(input.itinerary) || input.itinerary.length !== days) {
        throw new ValidationError('Lịch trình phải có đủ nội dung mỗi ngày.');
      }
      tour.itinerary = input.itinerary.map((day, i) => requiredText(day, 2000, 'Nội dung lịch trình', 'itinerary-' + i));
      if (input.stops !== undefined && (!Array.isArray(input.stops) || input.stops.length !== days)) {
        throw new ValidationError('Chọn điểm ghé cho từng ngày.');
      }
      tour.stops = input.stops?.map((place, i) => requiredText(place, 120, 'Điểm ghé', 'stop-' + i)) ?? tour.itinerary.map(() => tour.place);
    }
    if (input.cover) {
      if (typeof input.cover !== 'string' || input.cover.length > 1_398_134
        || !/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(input.cover)) {
        throw new ValidationError('Ảnh phải là JPG, PNG hoặc WebP tối đa 1 MB.', 'cover');
      }
      tour.cover = input.cover;
    }
    if (!await this.repository.saveTour(tourId, tour, !id)) throw new AppError(404, 'Không tìm thấy tour.');
    return { id: tourId };
  }

  async setVisibility(id, hidden) {
    this.requireRole('admin');
    if (typeof hidden !== 'boolean') throw new ValidationError('Trạng thái hiển thị không hợp lệ.');
    if (!await this.repository.setVisibility(id, hidden)) throw new AppError(404, 'Không tìm thấy tour.');
  }

  async saveDeparture(tourId, input) {
    this.requireRole('admin');
    const day = departureDay(input.day);
    const capacity = integerBetween(input.capacity, 1, 100, 'Sức chứa', 'capacity');
    if (day < this.today) throw new ValidationError('Không thể sửa lịch đã qua.', 'day');
    const edit = input.edit ?? false;
    if (typeof edit !== 'boolean') throw new ValidationError('Thao tác lịch không hợp lệ.');
    if (edit) {
      if (!await this.repository.changeDepartureCapacity(tourId, day, capacity)) {
        throw new ConflictError('Đợt đã bị xóa hoặc sức chứa thấp hơn số chỗ đã giữ.', 'capacity');
      }
      return;
    }
    if (!await this.repository.createDeparture(tourId, day, capacity)) {
      throw new ConflictError('Ngày này đã có đợt khởi hành hoặc tour đã bị xóa.', 'day');
    }
  }

  async placeBooking(input) {
    this.requireRole('customer');
    const booking = {
      tourId: requiredText(input.tourId, 70, 'Tour', 'tourId'),
      day: departureDay(input.day),
      name: requiredText(input.name, 80, 'Tên người đại diện', 'name'),
      phone: requiredText(input.phone, 16, 'Số điện thoại', 'phone'),
      adults: integerBetween(input.adults, 1, 100, 'Số người lớn', 'adults'),
      children: integerBetween(input.children, 0, 99, 'Số trẻ em', 'children'),
    };
    if (!/^[0-9+ ()-]{9,16}$/.test(booking.phone) || booking.phone.replace(/\D/g, '').length < 8) {
      throw new ValidationError('Số điện thoại không hợp lệ.', 'phone');
    }
    const id = 'MG' + crypto.randomUUID().replaceAll('-', '').toUpperCase();
    if (!await this.repository.placeBooking(id, this.actor.id, booking, this.today)) {
      throw new ConflictError('Đợt khởi hành đã đóng hoặc không còn đủ chỗ.', 'day');
    }
    return { id };
  }

  async removeDeparture(tourId, value) {
    this.requireRole('admin');
    const day = departureDay(value);
    if (!await this.repository.removeDeparture(tourId, day)) {
      throw new ConflictError('Đợt không tồn tại hoặc đã có lịch sử đặt chỗ.');
    }
  }

  async updateBooking(id, action) {
    if (!['confirm', 'collect', 'refund', 'cancel'].includes(action)) {
      throw new ValidationError('Thao tác đơn không hợp lệ.');
    }
    const role = action === 'cancel' && this.actor?.role === 'customer' ? 'customer' : 'admin';
    this.requireRole(role);
    const ownerId = role === 'customer' ? this.actor.id : null;
    if (!await this.repository.updateBooking(id, action, ownerId)) {
      throw new ConflictError('Không thể thao tác với đơn này ở trạng thái hiện tại.');
    }
  }
}
