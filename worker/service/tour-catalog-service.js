import { AccountRole } from '../domain/account.js';
import { Departure } from '../domain/departure.js';
import { AppError, ConflictError, ValidationError } from '../domain/errors.js';
import { Tour } from '../domain/tour.js';

export class TourCatalogService {
  /** @param {import('../ports.js').TourCatalogPort} repository */
  constructor(repository, access, today) {
    this.repository = repository;
    this.access = access;
    this.today = today;
  }

  catalog() {
    return this.repository.catalog(this.access.actor?.role === AccountRole.ADMIN);
  }

  async saveTour(id, input) {
    this.access.requireRole(AccountRole.ADMIN);
    const tour = new Tour(id || crypto.randomUUID(), input);
    if (!await this.repository.saveTour(tour, !id)) throw new AppError(404, 'Không tìm thấy tour.');
    return { id: tour.id };
  }

  async setVisibility(id, hidden) {
    this.access.requireRole(AccountRole.ADMIN);
    if (typeof hidden !== 'boolean') throw new ValidationError('Trạng thái hiển thị không hợp lệ.');
    if (!await this.repository.setVisibility(id, hidden)) throw new AppError(404, 'Không tìm thấy tour.');
  }

  async saveDeparture(tourId, input) {
    this.access.requireRole(AccountRole.ADMIN);
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

  async removeDeparture(tourId, value) {
    this.access.requireRole(AccountRole.ADMIN);
    if (!await this.repository.removeDeparture(tourId, Departure.validateDay(value))) {
      throw new ConflictError('Đợt không tồn tại hoặc đã có lịch sử đặt chỗ.');
    }
  }
}
