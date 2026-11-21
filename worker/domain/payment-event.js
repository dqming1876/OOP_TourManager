import { ValidationError } from './errors.js';
import { calendarDay, integerBetween } from './validation.js';

export const PaymentKind = Object.freeze({ COLLECT: 'collect', REFUND: 'refund' });

export class PaymentEvent {
  constructor({ date, kind, amount }) {
    this.date = calendarDay(date, 'Ngày ghi nhận không hợp lệ.', 'date');
    if (!Object.values(PaymentKind).includes(kind)) throw new ValidationError('Loại nghiệp vụ thanh toán không hợp lệ.');
    this.kind = kind;
    this.amount = integerBetween(amount, 1, Number.MAX_SAFE_INTEGER, 'Số tiền', 'amount');
    Object.freeze(this);
  }

  get signedAmount() {
    return this.kind === PaymentKind.REFUND ? -this.amount : this.amount;
  }
}
