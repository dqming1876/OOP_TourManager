export class AppError extends Error {
  constructor(status, message, field) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
    this.field = field;
  }
}

export class ValidationError extends AppError {
  constructor(message, field) {
    super(400, message, field);
  }
}

export class AccessError extends AppError {}
export class ConflictError extends AppError {
  constructor(message, field) {
    super(409, message, field);
  }
}
