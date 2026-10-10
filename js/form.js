/* ============================================
   FORM VALIDATION
   Валидация формы записи
   ============================================ */

(function () {
  'use strict';

  const form = document.querySelector('.form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const name = document.getElementById('name');
    const contactMethod = document.getElementById('contact-method');
    const contactValue = document.getElementById('contact-value');

    // Remove previous errors
    form.querySelectorAll('.form__error').forEach(function (el) {
      el.remove();
    });

    let isValid = true;

    // Validate name
    if (!name.value.trim()) {
      addError(name, 'Пожалуйста, введите ваше имя');
      isValid = false;
    }

    // Validate contact method
    if (!contactMethod.value) {
      addError(contactMethod, 'Выберите способ связи');
      isValid = false;
    }

    // Validate contact value
    if (!contactValue.value.trim()) {
      addError(contactValue, 'Укажите ваш контакт для связи');
      isValid = false;
    }

    if (isValid) {
      // Show success message
      const successMsg = document.createElement('p');
      successMsg.className = 'form__success';
      successMsg.style.cssText = 'color: var(--color-accent-green); text-align: center; font-weight: 500; margin-top: var(--space-md);';
      successMsg.textContent = 'Спасибо! Я свяжусь с вами в ближайшее время.';

      // Remove previous success message if exists
      const prev = form.querySelector('.form__success');
      if (prev) prev.remove();

      form.appendChild(successMsg);
      form.reset();
    }
  });

  function addError(input, message) {
    const error = document.createElement('p');
    error.className = 'form__error';
    error.textContent = message;
    input.parentNode.appendChild(error);
    input.style.borderColor = '#E53935';

    // Reset border on focus
    input.addEventListener('focus', function () {
      input.style.borderColor = '';
      const existing = input.parentNode.querySelector('.form__error');
      if (existing) existing.remove();
    }, { once: true });
  }
})();
