import { AccountRole } from '../domain/account.js';
import { Booking } from '../domain/booking.js';
import { ConflictError } from '../domain/errors.js';

export class BookingService {
  /** @param {import('../ports.js').BookingPort} repository */
  constructor(repository, access, today) {
    this.repository = repository;
    this.access = access;
    this.today = today;
  }

  bookings() {
    const scope = this.access.bookingScope();
    return this.repository.listBookings(scope);
  }

  async placeBooking(input) {
    this.access.requireRole(AccountRole.CUSTOMER);
    const id = 'MG' + crypto.randomUUID().replaceAll('-', '').toUpperCase();
    const booking = Booking.request(id, this.access.actor.id, input);
    if (!await this.repository.placeBooking(booking, this.today)) {
      throw new ConflictError('Đợt khởi hành đã đóng hoặc không còn đủ chỗ.', 'day');
    }
    return { id };
  }

  paymentHistory(bookingId) {
    this.access.requireRole(AccountRole.ADMIN);
    return this.repository.paymentHistory(bookingId);
  }

  async updateBooking(id, action) {
    const customerCancel = action === 'cancel' && this.access.actor?.role === AccountRole.CUSTOMER;
    const rule = Booking.transition(action, customerCancel);
    this.access.requireRole(customerCancel ? AccountRole.CUSTOMER : AccountRole.ADMIN);
    const ownerId = customerCancel ? this.access.actor.id : null;
    if (!await this.repository.updateBooking(id, rule, ownerId, this.today)) {
      throw new ConflictError('Không thể thao tác với đơn ở trạng thái hoặc ngày khởi hành hiện tại.');
    }
  }
}
