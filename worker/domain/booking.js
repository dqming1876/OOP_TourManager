import { Departure } from './departure.js';
import { ConflictError, ValidationError } from './errors.js';
import { integerBetween, requiredText } from './validation.js';

export const BookingStatus = Object.freeze({
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  CANCELLED: 'cancelled',
});

const { PENDING, CONFIRMED, CANCELLED } = BookingStatus;

const transitions = Object.freeze({
  confirm: Object.freeze({ from: PENDING, to: CONFIRMED, paid: false, nextPaid: false, checkDay: true }),
  collect: Object.freeze({ from: CONFIRMED, to: CONFIRMED, paid: false, nextPaid: true }),
  refund: Object.freeze({ from: CONFIRMED, to: CONFIRMED, paid: true, nextPaid: false }),
  cancel: Object.freeze({ from: PENDING, alsoFrom: CONFIRMED, to: CANCELLED, paid: false, nextPaid: false }),
});

export class Booking {
  constructor({
    id, userId, tourId, day, title, name, phone, adults, children,
    unitPrice, status = PENDING, paid = false,
  }) {
    if (!Object.values(BookingStatus).includes(status) || typeof paid !== 'boolean' || (paid && status !== CONFIRMED)) {
      throw new ValidationError('Trạng thái đơn và thanh toán không tương thích.');
    }
    this.adults = integerBetween(adults, 1, Number.MAX_SAFE_INTEGER, 'Số người lớn', 'adults');
    this.children = integerBetween(children, 0, Number.MAX_SAFE_INTEGER, 'Số trẻ em', 'children');
    this.unitPrice = unitPrice === undefined ? undefined
      : integerBetween(unitPrice, 1, Number.MAX_SAFE_INTEGER, 'Giá chốt', 'unitPrice');
    Object.assign(this, { id, userId, tourId, day, title, name, phone, status, paid });
    Object.freeze(this);
  }

  static request(id, userId, input) {
    const phone = requiredText(input.phone, 16, 'Số điện thoại', 'phone');
    if (!/^[0-9+ ()-]{9,16}$/.test(phone) || phone.replace(/\D/g, '').length < 8) {
      throw new ValidationError('Số điện thoại không hợp lệ.', 'phone');
    }
    return new Booking({
      id, userId, phone,
      tourId: requiredText(input.tourId, 70, 'Tour', 'tourId'),
      day: Departure.validateDay(input.day),
      name: requiredText(input.name, 80, 'Tên người đại diện', 'name'),
      adults: integerBetween(input.adults, 1, 100, 'Số người lớn', 'adults'),
      children: integerBetween(input.children, 0, 99, 'Số trẻ em', 'children'),
    });
  }

  static transition(action, ownBookingOnly) {
    if (!Object.hasOwn(transitions, action)) throw new ValidationError('Thao tác đơn không hợp lệ.');
    const rule = transitions[action];
    if (action === 'cancel' && ownBookingOnly) return Object.freeze({ ...rule, alsoFrom: PENDING });
    return rule;
  }

  get people() {
    return this.adults + this.children;
  }

  get total() {
    if (this.unitPrice === undefined) throw new ConflictError('Đơn chưa có giá chốt.');
    return this.people * this.unitPrice;
  }
}
