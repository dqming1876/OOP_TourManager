// Structural contracts owned by the application. Adapters meet a contract
// by implementing its methods. DTOs are plain records at the HTTP boundary.

/**
 * @typedef {object} BookingPort
 * @property {(ownerId: string|null) => Promise<object[]>} listBookings
 * @property {(booking: import('./domain/booking.js').Booking, today: string) => Promise<boolean>} placeBooking
 * @property {(id: string, rule: object, ownerId: string|null, today: string) => Promise<boolean>} updateBooking
 * @property {(id: string) => Promise<object[]>} paymentHistory
 */

/**
 * @typedef {object} TourCatalogPort
 * @property {(includeHidden: boolean) => Promise<object[]>} catalog
 * @property {(tour: import('./domain/tour.js').Tour, create: boolean) => Promise<boolean>} saveTour
 * @property {(id: string, hidden: boolean) => Promise<boolean>} setVisibility
 * @property {(departure: import('./domain/departure.js').Departure) => Promise<boolean>} createDeparture
 * @property {(departure: import('./domain/departure.js').Departure) => Promise<boolean>} changeDepartureCapacity
 * @property {(id: string, day: string) => Promise<boolean>} removeDeparture
 */

/**
 * @typedef {object} ReportFilter
 * @property {string} from
 * @property {string} to
 * @property {string} tourId
 * @property {string} today
 */

/** @typedef {{load: (filter: ReportFilter) => Promise<object>}} ReportPort */

/**
 * @typedef {object} AccountsPort
 * @property {(id: string) => Promise<object|null>} findPublicById
 * @property {(username: string) => Promise<object|null>} findByUsername
 * @property {(account: object) => Promise<boolean>} create
 * @property {(id: string, profile: object) => Promise<unknown>} updateProfile
 */

export {};
