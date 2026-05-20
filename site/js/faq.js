/* ============================================
   FAQ ACCORDION
   Раскрытие/закрытие вопросов
   ============================================ */

(function () {
  "use strict";

  const faqItems = document.querySelectorAll(".faq-item");

  faqItems.forEach(function (item) {
    const button = item.querySelector(".faq-item__button");
    const answer = item.querySelector(".faq-item__answer");

    if (!button || !answer) return;

    button.addEventListener("click", function () {
      const isOpen = item.classList.contains("faq-item--open");

      // Close all other items
      faqItems.forEach(function (otherItem) {
        if (otherItem !== item) {
          otherItem.classList.remove("faq-item--open");
          const otherButton = otherItem.querySelector(".faq-item__button");
          if (otherButton) otherButton.setAttribute("aria-expanded", "false");
          const otherAnswer = otherItem.querySelector(".faq-item__answer");
          if (otherAnswer) {
            otherAnswer.style.maxHeight = "0";
            otherAnswer.style.opacity = "0";
          }
        }
      });

      // Toggle current item
      if (isOpen) {
        item.classList.remove("faq-item--open");
        button.setAttribute("aria-expanded", "false");
        answer.style.maxHeight = "0";
        answer.style.opacity = "0";
      } else {
        item.classList.add("faq-item--open");
        button.setAttribute("aria-expanded", "true");
        answer.style.maxHeight = answer.scrollHeight + "px";
        answer.style.opacity = "1";
      }
    });
  });
})();
