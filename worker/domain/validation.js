import { ValidationError } from './errors.js';

export function validCalendarDay(value) {
  return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
}

export function calendarDay(value, message, field) {
  if (!validCalendarDay(value)) throw new ValidationError(message, field);
  return value;
}

export function requiredText(value, limit, label, field) {
  if (typeof value !== 'string' || !value.trim() || value.trim().length > limit) {
    throw new ValidationError(label + ' không hợp lệ.', field);
  }
  return value.trim();
}

export function integerBetween(value, min, max, label, field) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new ValidationError(label + ' phải từ ' + min + ' đến ' + max + '.', field);
  }
  return value;
}
