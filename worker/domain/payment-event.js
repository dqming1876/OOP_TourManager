export const PaymentKind = Object.freeze({ COLLECT: 'collect', REFUND: 'refund' });

export class PaymentEvent {
  constructor({ date, kind, amount }) {
    this.date = date;
    this.kind = kind;
    this.amount = amount;
  }

  get signedAmount() {
    return this.kind === PaymentKind.REFUND ? -this.amount : this.amount;
  }
}
