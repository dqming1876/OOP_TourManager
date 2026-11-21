import { ValidationError } from './errors.js';
import { integerBetween, requiredText } from './validation.js';

export class Destination {
  constructor(province, name, field = 'place') {
    this.province = requiredText(province, 80, 'Tỉnh thành', 'province');
    this.name = requiredText(name, 120, 'Điểm đến', field);
    Object.freeze(this);
  }
}

export class TourStop {
  constructor(dayNumber, activity, province, place) {
    this.dayNumber = integerBetween(dayNumber, 1, 30, 'Thứ tự ngày', 'days');
    this.activity = requiredText(activity, 2000, 'Nội dung lịch trình', 'itinerary-' + (dayNumber - 1));
    this.destination = new Destination(province, place, 'stop-' + (dayNumber - 1));
    Object.freeze(this);
  }

  toWriteRow() {
    return { dayNumber: this.dayNumber, place: this.destination.name, activity: this.activity };
  }
}

export class Tour {
  #details;
  #stops;

  constructor(id, input) {
    const destination = new Destination(input.province, input.place);
    this.id = id;
    const details = {
      title: requiredText(input.title, 120, 'Tên tour', 'title'),
      province: destination.province,
      place: destination.name,
      price: integerBetween(input.price, 1, 1_000_000_000, 'Giá tour', 'price'),
      desc: requiredText(input.desc, 4000, 'Mô tả', 'desc'),
      days: integerBetween(input.days, 1, 30, 'Số ngày', 'days'),
    };
    for (const field of ['category', 'pickup', 'includes', 'excludes', 'coverSource']) {
      if (input[field]) details[field] = requiredText(input[field], 2000, field, field);
    }
    if (input.cover) details.cover = this.#validatedCover(input.cover);
    this.#details = Object.freeze(details);
    const stops = this.#buildItinerary(input, destination);
    this.#stops = stops ? Object.freeze(stops) : null;
    Object.freeze(this);
  }

  get details() {
    return this.#details;
  }

  get stops() {
    return this.#stops;
  }

  #buildItinerary({ itinerary, stops }, destination) {
    if (itinerary === undefined) return null;
    if (!Array.isArray(itinerary) || itinerary.length !== this.details.days) {
      throw new ValidationError('Lịch trình phải có đủ nội dung mỗi ngày.');
    }
    if (stops !== undefined && (!Array.isArray(stops) || stops.length !== itinerary.length)) {
      throw new ValidationError('Chọn điểm ghé cho từng ngày.');
    }
    return itinerary.map((activity, index) => {
      const place = stops ? stops[index] : destination.name;
      return new TourStop(index + 1, activity, destination.province, place);
    });
  }

  #validatedCover(cover) {
    if (typeof cover !== 'string' || cover.length > 1_398_134
      || !/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(cover)) {
      throw new ValidationError('Ảnh phải là JPG, PNG hoặc WebP tối đa 1 MB.', 'cover');
    }
    return cover;
  }
}
