import { AccountRole } from '../domain/account.js';
import { Booking } from '../domain/booking.js';
import { Departure } from '../domain/departure.js';
import { AccessError, AppError, ConflictError, ValidationError } from '../domain/errors.js';
import { Tour } from '../domain/tour.js';

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
    return this.repository.catalog(this.actor?.role === AccountRole.ADMIN);
  }

  bookings() {
    if (!this.actor) throw new AccessError(401, 'Vui lòng đăng nhập.');
    return this.repository.listBookings(this.actor.bookingScope());
  }

  async saveTour(id, input) {
    this.requireRole(AccountRole.ADMIN);
    const tour = new Tour(id || crypto.randomUUID(), input);
    if (!await this.repository.saveTour(tour, !id)) throw new AppError(404, 'Không tìm thấy tour.');
    return { id: tour.id };
  }

  async setVisibility(id, hidden) {
    this.requireRole(AccountRole.ADMIN);
    if (typeof hidden !== 'boolean') throw new ValidationError('Trạng thái hiển thị không hợp lệ.');
    if (!await this.repository.setVisibility(id, hidden)) throw new AppError(404, 'Không tìm thấy tour.');
  }

  async saveDeparture(tourId, input) {
    this.requireRole(AccountRole.ADMIN);
    const departure = new Departure(tourId, input.day, input.capacity);
    departure.requireOpenDate(this.today);
    const edit = input.edit ?? false;
    if (typeof edit !== 'boolean') throw new ValidationError('Thao tác lịch không hợp lệ.');
    if (edit) {
      if (!await this.repository.changeDepartureCapacity(departure)) {
        throw new ConflictError('Đợt đã bị xóa hoặc sức chứa thấp hơn số chỗ đã giữ.', 'capacity');
      }
      return;
    }
    if (!await this.repository.createDeparture(departure)) {
      throw new ConflictError('Ngày này đã có đợt khởi hành hoặc tour đã bị xóa.', 'day');
    }
  }

  async placeBooking(input) {
    this.requireRole(AccountRole.CUSTOMER);
    const id = 'MG' + crypto.randomUUID().replaceAll('-', '').toUpperCase();
    const booking = Booking.request(id, this.actor.id, input);
    if (!await this.repository.placeBooking(booking, this.today)) {
      throw new ConflictError('Đợt khởi hành đã đóng hoặc không còn đủ chỗ.', 'day');
    }
    return { id };
  }

  async removeDeparture(tourId, value) {
    this.requireRole(AccountRole.ADMIN);
    if (!await this.repository.removeDeparture(tourId, Departure.validateDay(value))) {
      throw new ConflictError('Đợt không tồn tại hoặc đã có lịch sử đặt chỗ.');
    }
  }

  paymentHistory(bookingId) {
    this.requireRole(AccountRole.ADMIN);
    return this.repository.paymentHistory(bookingId);
  }

  async updateBooking(id, action) {
    const customerCancel = action === 'cancel' && this.actor?.role === AccountRole.CUSTOMER;
    const rule = Booking.transition(action, customerCancel);
    this.requireRole(customerCancel ? AccountRole.CUSTOMER : AccountRole.ADMIN);
    const ownerId = customerCancel ? this.actor.id : null;
    if (!await this.repository.updateBooking(id, rule, ownerId, this.today)) {
      throw new ConflictError('Không thể thao tác với đơn ở trạng thái hoặc ngày khởi hành hiện tại.');
    }
  }
}
