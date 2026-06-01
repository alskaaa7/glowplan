// ------------------------------------------------------------
// static/js/main.js — клиентская логика
// FRONTEND (Разработчик 1 (Самира)): UI-взаимодействия
// ------------------------------------------------------------

// автоматически убираем flash-сообщения через 4 секунды
document.addEventListener("DOMContentLoaded", () => {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = "0";
            flash.style.transition = "opacity .3s";
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    });

    // чек-лист: визуальное обновление при клике (Разработчик 1 (Самира))
    const checklistItems = document.querySelectorAll(".checklist-item");
    checklistItems.forEach((item) => {
        item.addEventListener("click", () => {
            const checkbox = item.querySelector('input[type="checkbox"]');
            // переключаем визуальный класс немедленно (до сабмита формы)
            item.classList.toggle("checklist-item--done", checkbox.checked);
        });
    });
});
