const wholeNumberFormat = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 });
const wholeNumber = value => wholeNumberFormat.format(value);
const todayInVietnam = () => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date());

let fieldErrorSequence = 0;

function showFieldError(field, message) {
  if (!message && !field.dataset.fieldError) return;
  const id = field.dataset.fieldError || (field.dataset.fieldError = 'field-error-' + ++fieldErrorSequence);
  let error = document.getElementById(id);
  if (!error && message) {
    error = document.createElement('span');
    error.id = id;
    error.className = 'field-error';
    error.setAttribute('aria-live', 'polite');
    (field.closest('.stepper') || field).after(error);
    const descriptions = [field.getAttribute('aria-describedby'), id].filter(Boolean);
    field.setAttribute('aria-describedby', descriptions.join(' '));
  }
  if (error) error.textContent = message || '';
  if (message) field.setAttribute('aria-invalid', 'true');
  else field.removeAttribute('aria-invalid');
}

function fieldValidationMessage(field) {
  if (field.type === 'file') {
    const file = field.files?.[0];
    if (file && (file.size > 1024 * 1024 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type))) {
      return 'Chọn ảnh JPG, PNG hoặc WebP tối đa 1 MB.';
    }
  }
  if (field.validity.badInput) return 'Giá trị nhập không hợp lệ.';
  if (field.required && !field.value.trim()) return 'Vui lòng nhập hoặc chọn giá trị.';
  if (field.type === 'date' && field.value && field.min && field.value < field.min) {
    return 'Ngày sớm nhất là ' + date(field.min) + '.';
  }
  if (field.validity.rangeUnderflow || field.validity.rangeOverflow) {
    return 'Nhập số từ ' + wholeNumber(field.min) + ' đến ' + wholeNumber(field.max) + '.';
  }
  if (field.validity.stepMismatch) return 'Vui lòng nhập số nguyên.';
  if (field.validity.tooShort) return 'Nhập ít nhất ' + field.minLength + ' ký tự.';
  if (field.validity.tooLong) return 'Nhập tối đa ' + field.maxLength + ' ký tự.';
  if (field.validity.typeMismatch) return 'Định dạng không hợp lệ.';
  if (field.dataset.phone !== undefined && field.value.trim()) {
    const phone = field.value.trim();
    if (!/^[0-9+ ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 8) {
      return 'Nhập ít nhất 8 chữ số. Có thể dùng +, khoảng trắng, ngoặc và dấu gạch.';
    }
  }
  return field.validity.valid ? '' : 'Vui lòng kiểm tra lại ô này.';
}

function validateMingoForm(form, extra = {}) {
  let firstInvalid;
  for (const field of form.querySelectorAll('input, select, textarea')) {
    if (!field.willValidate) continue;
    const message = fieldValidationMessage(field) || extra[field.name];
    showFieldError(field, message);
    if (message && !firstInvalid) firstInvalid = field;
  }
  if (firstInvalid) firstInvalid.focus();
  return !firstInvalid;
}

function showSubmissionError(form, error) {
  const field = error.field && form.elements.namedItem(error.field);
  if (field instanceof HTMLElement) {
    showFieldError(field, error.message);
    field.focus();
    return;
  }
  const summary = form.querySelector('.submission-error');
  if (summary) summary.textContent = error.message;
  else toast(error.message);
}

function refreshFieldError(event) {
  const field = event.target;
  if (field.form?.hasAttribute('data-validated') && field.hasAttribute('aria-invalid')) {
    showFieldError(field, fieldValidationMessage(field));
  }
}

document.addEventListener('input', refreshFieldError);
document.addEventListener('change', refreshFieldError);
