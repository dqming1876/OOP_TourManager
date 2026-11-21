import { ValidationError } from './errors.js';
import { calendarDay, integerBetween } from './validation.js';

export class Departure {
  constructor(tourId, day, capacity, reserved = 0) {
    this.tourId = tourId;
    this.day = Departure.validateDay(day);
    this.capacity = integerBetween(capacity, 1, 100, 'Sức chứa', 'capacity');
    this.reserved = reserved;
  }

  static validateDay(day) {
    return calendarDay(day, 'Ngày khởi hành không hợp lệ.', 'day');
  }

  requireOpenDate(today) {
    if (this.day < today) throw new ValidationError('Không thể sửa lịch đã qua.', 'day');
  }

  get remaining() {
    return this.capacity - this.reserved;
  }
}
