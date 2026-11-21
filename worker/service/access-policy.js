import { AccessError } from '../domain/errors.js';

export class AccessPolicy {
  constructor(actor) {
    this.actor = actor;
  }

  requireRole(role) {
    if (!this.actor) throw new AccessError(401, 'Vui lòng đăng nhập.');
    if (this.actor.role !== role) throw new AccessError(403, 'Bạn không có quyền thực hiện thao tác này.');
  }

  bookingScope() {
    if (!this.actor) throw new AccessError(401, 'Vui lòng đăng nhập.');
    return this.actor.bookingScope();
  }
}
