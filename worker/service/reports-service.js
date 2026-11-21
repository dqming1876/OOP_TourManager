import { ValidationError } from '../domain/errors.js';
import { calendarDay } from '../domain/validation.js';

export class ReportsService {
  constructor(operations, repository) {
    this.operations = operations;
    this.repository = repository;
  }

  async load(params) {
    this.operations.requireRole('admin');
    const from = params.get('from') ? calendarDay(params.get('from'), 'Ngày bắt đầu không hợp lệ.', 'from') : '0001-01-01';
    const to = params.get('to') ? calendarDay(params.get('to'), 'Ngày kết thúc không hợp lệ.', 'to') : '9999-12-31';
    const tourId = params.get('tour') || '';
    if (from > to || tourId.length > 70) throw new ValidationError('Bộ lọc báo cáo không hợp lệ.');
    return this.repository.load({ from, to, tourId, today: this.operations.today });
  }
}
