import { ValidationError } from './errors.js';
import { validCalendarDay } from './validation.js';

export const AccountRole = Object.freeze({ ADMIN: 'admin', CUSTOMER: 'customer' });

const profileFields = {
  name: ['Họ tên', 80], email: ['Email', 120], phone: ['Số điện thoại', 20],
  address: ['Địa chỉ', 250], birthday: ['Ngày sinh', 10],
};

function validateProfile(body) {
  const invalid = field => new ValidationError(profileFields[field][0] + ' không hợp lệ.', field);
  const profile = {};
  for (const [field, [, limit]] of Object.entries(profileFields)) {
    const value = body[field] ?? '';
    if (typeof value !== 'string' || value.trim().length > limit) throw invalid(field);
    profile[field] = value.trim();
  }
  const { name, email, phone, birthday } = profile;
  if (!name) throw invalid('name');
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw invalid('email');
  if (phone && (!/^[0-9+ ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 8)) throw invalid('phone');
  if (birthday && !validCalendarDay(birthday)) throw invalid('birthday');
  return profile;
}

// Both account types have a public session identity, but expose different scopes.
class Account {
  constructor(id, name, username, role) {
    Object.assign(this, { id, name, username, role });
  }

  toPublic() {
    return { id: this.id, name: this.name, username: this.username, role: this.role };
  }

  /** @returns {string|null} Customer ID for own bookings, or null for all bookings. */
  bookingScope() {
    return this.id;
  }
}

export class CustomerAccount extends Account {
  constructor({ id, name, username, email, phone, address, birthday }) {
    super(id, name, username, AccountRole.CUSTOMER);
    this.profile = Object.freeze({ email, phone, address, birthday });
    Object.freeze(this);
  }

  validateUpdate(input) {
    return validateProfile(input);
  }

  toPublic() {
    return { ...super.toPublic(), ...this.profile };
  }
}

export class AdministratorAccount extends Account {
  constructor(username) {
    super('admin', 'Quản trị viên', username, AccountRole.ADMIN);
    Object.freeze(this);
  }

  bookingScope() {
    return null;
  }
}
