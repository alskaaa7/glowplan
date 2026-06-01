// ------------------------------------------------------------
// static/js/main.js — клиентская логика
// FRONTEND (Разработчик 1 (Самира)): UI-взаимодействия
// FRONTEND (Разработчик 3 (Даша)): LocalStorage — тема, кэш уведомлений,
//   свёрнутые секции, черновики форм, кэш API пользователей
// ------------------------------------------------------------

// ============================================================
// LocalStorage — namespace-обёртка (Разработчик 3 (Даша))
// все ключи хранятся с префиксом "gp:" чтобы не конфликтовать
// ============================================================
const LS = {
    PREFIX: "gp:",

    set(key, value) {
        try {
            localStorage.setItem(this.PREFIX + key, JSON.stringify(value));
        } catch (e) {
            // если квота превышена — молча игнорируем
            console.warn("LocalStorage write failed:", e);
        }
    },

    get(key, fallback = null) {
        try {
            const raw = localStorage.getItem(this.PREFIX + key);
            return raw !== null ? JSON.parse(raw) : fallback;
        } catch (e) {
            return fallback;
        }
    },

    remove(key) {
        localStorage.removeItem(this.PREFIX + key);
    },

    clear() {
        // удаляем только наши ключи
        Object.keys(localStorage)
            .filter(k => k.startsWith(this.PREFIX))
            .forEach(k => localStorage.removeItem(k));
    }
};


// ============================================================
// Тема интерфейса: светлая / тёмная (Разработчик 3 (Даша))
// сохраняется в LocalStorage под ключом "gp:theme"
// ============================================================
const Theme = {
    DARK_CLASS: "theme-dark",
    KEY: "theme",

    init() {
        // применяем сохранённую тему сразу при загрузке
        const saved = LS.get(this.KEY, "light");
        if (saved === "dark") document.body.classList.add(this.DARK_CLASS);
        this._updateToggle(saved);
    },

    toggle() {
        const isDark = document.body.classList.toggle(this.DARK_CLASS);
        const next = isDark ? "dark" : "light";
        LS.set(this.KEY, next);
        this._updateToggle(next);
    },

    _updateToggle(theme) {
        const btn = document.getElementById("theme-toggle");
        if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
    }
};


// ============================================================
// Скрытые уведомления: запоминаем какие баннеры закрыл юзер
// FRONTEND (Разработчик 3 (Даша)): кэш скрытых id баннеров
// ============================================================
const DismissedBanners = {
    KEY: "dismissed_banners",

    _load() {
        return LS.get(this.KEY, {});
    },

    dismiss(id) {
        const map = this._load();
        // храним timestamp — через 24 часа баннер снова может появиться
        map[id] = Date.now();
        LS.set(this.KEY, map);
    },

    isDismissed(id) {
        const map = this._load();
        if (!map[id]) return false;
        const age = Date.now() - map[id];
        return age < 24 * 60 * 60 * 1000; // 24 часа
    },

    init() {
        // скрываем баннеры, которые уже были закрыты за последние 24 ч
        document.querySelectorAll(".banner[data-banner-id]").forEach(banner => {
            const id = banner.dataset.bannerId;
            if (this.isDismissed(id)) {
                banner.style.display = "none";
            }
            // вешаем кнопку закрытия
            const closeBtn = banner.querySelector(".banner__close");
            if (closeBtn) {
                closeBtn.addEventListener("click", () => {
                    this.dismiss(id);
                    banner.style.display = "none";
                });
            }
        });
    }
};


// ============================================================
// Свёрнутые / развёрнутые секции (Разработчик 3 (Даша))
// ============================================================
const Collapsible = {
    KEY: "collapsed_sections",

    _load() {
        return LS.get(this.KEY, []);
    },

    _save(list) {
        LS.set(this.KEY, list);
    },

    toggle(sectionId) {
        const list = this._load();
        const idx = list.indexOf(sectionId);
        if (idx === -1) list.push(sectionId);
        else list.splice(idx, 1);
        this._save(list);
        return idx === -1; // true = теперь свёрнута
    },

    init() {
        const collapsed = this._load();
        collapsed.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add("is-collapsed");
        });

        document.querySelectorAll("[data-collapse-target]").forEach(btn => {
            btn.addEventListener("click", () => {
                const target = document.getElementById(btn.dataset.collapseTarget);
                if (!target) return;
                const nowCollapsed = this.toggle(btn.dataset.collapseTarget);
                target.classList.toggle("is-collapsed", nowCollapsed);
                btn.classList.toggle("is-collapsed", nowCollapsed);
            });
        });
    }
};


// ============================================================
// Черновики форм — автосохранение в LocalStorage (Разработчик 3 (Даша))
// восстанавливаем текст при следующем открытии страницы
// ============================================================
const FormDraft = {
    KEY_PREFIX: "draft_",

    save(formId, data) {
        LS.set(this.KEY_PREFIX + formId, data);
    },

    load(formId) {
        return LS.get(this.KEY_PREFIX + formId, null);
    },

    clear(formId) {
        LS.remove(this.KEY_PREFIX + formId);
    },

    init() {
        // автосохранение textarea и text-input с атрибутом data-draft-form
        document.querySelectorAll("[data-draft-form]").forEach(field => {
            const formId = field.dataset.draftForm;

            // восстановить черновик
            const draft = this.load(formId);
            if (draft && draft[field.name]) {
                field.value = draft[field.name];
            }

            // сохранять при каждом изменении
            field.addEventListener("input", () => {
                const existing = this.load(formId) || {};
                existing[field.name] = field.value;
                this.save(formId, existing);
            });
        });

        // при отправке формы — очищаем черновик
        document.querySelectorAll("form[data-draft-id]").forEach(form => {
            form.addEventListener("submit", () => {
                this.clear(form.dataset.draftId);
            });
        });
    }
};


// ============================================================
// Виджет User API (Разработчик 3 (Даша))
// обёртка над /api/users для демонстрации REST API в браузере
// кэшируем список в LocalStorage на 5 минут
// ============================================================
const UserApiWidget = {
    CACHE_KEY:  "api_users_cache",
    CACHE_TTL:  5 * 60 * 1000, // 5 минут

    async fetchUsers(forceRefresh = false) {
        if (!forceRefresh) {
            const cached = LS.get(this.CACHE_KEY);
            if (cached && (Date.now() - cached.ts) < this.CACHE_TTL) {
                return cached.users;
            }
        }
        const resp = await fetch("/api/users");
        const data = await resp.json();
        if (resp.ok) {
            LS.set(this.CACHE_KEY, { users: data.users, ts: Date.now() });
        }
        return data.users || [];
    },

    async fetchUser(id) {
        const resp = await fetch(`/api/users/${id}`);
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.message || "Не найдено");
        return data.user;
    },

    async createUser(payload) {
        const resp = await fetch("/api/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.message || "Ошибка создания");
        // сбрасываем кэш
        LS.remove(this.CACHE_KEY);
        return data.user;
    },

    init() {
        const container = document.getElementById("user-api-widget");
        if (!container) return;

        const listEl = document.getElementById("api-user-list");
        const formEl = document.getElementById("api-create-user-form");
        const refreshBtn = document.getElementById("api-refresh-btn");
        const errorEl = document.getElementById("api-error");

        const showError = (msg) => {
            if (errorEl) { errorEl.textContent = msg; errorEl.style.display = "block"; }
        };
        const hideError = () => {
            if (errorEl) errorEl.style.display = "none";
        };

        const renderUsers = (users) => {
            if (!listEl) return;
            if (!users.length) {
                listEl.innerHTML = "<p class='hint'>Нет пользователей</p>";
                return;
            }
            listEl.innerHTML = users.map(u => `
                <div class="api-user-row">
                    <span class="api-user-row__id">#${u.id}</span>
                    <span class="api-user-row__name">${_escHtml(u.name)}</span>
                    <span class="api-user-row__email">${_escHtml(u.email)}</span>
                    ${u.age != null ? `<span class="api-user-row__age">${u.age} лет</span>` : ""}
                </div>
            `).join("");
        };

        // загружаем список при инициализации
        (async () => {
            try {
                const users = await this.fetchUsers();
                renderUsers(users);
            } catch (e) {
                showError(e.message);
            }
        })();

        // обновить список вручную
        if (refreshBtn) {
            refreshBtn.addEventListener("click", async () => {
                hideError();
                try {
                    const users = await this.fetchUsers(true);
                    renderUsers(users);
                } catch (e) {
                    showError(e.message);
                }
            });
        }

        // форма создания пользователя
        if (formEl) {
            formEl.addEventListener("submit", async (e) => {
                e.preventDefault();
                hideError();
                const payload = {
                    name:  formEl.querySelector("[name=api_name]")?.value.trim(),
                    email: formEl.querySelector("[name=api_email]")?.value.trim(),
                    age:   formEl.querySelector("[name=api_age]")?.value || null,
                };
                try {
                    await this.createUser(payload);
                    formEl.reset();
                    const users = await this.fetchUsers(true);
                    renderUsers(users);
                } catch (e) {
                    showError(e.message);
                }
            });
        }
    }
};

/** экранируем HTML чтобы не вставлять пользовательский текст как разметку */
function _escHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}


// ============================================================
// Инициализация всех модулей при загрузке страницы
// ============================================================
document.addEventListener("DOMContentLoaded", () => {

    // ---- тема (Разработчик 3 (Даша)) ----
    Theme.init();

    // кнопка переключения темы в navbar
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) themeToggle.addEventListener("click", () => Theme.toggle());

    // ---- баннеры (Разработчик 3 (Даша)) ----
    DismissedBanners.init();

    // ---- сворачиваемые секции (Разработчик 3 (Даша)) ----
    Collapsible.init();

    // ---- черновики форм (Разработчик 3 (Даша)) ----
    FormDraft.init();

    // ---- User API widget (Разработчик 3 (Даша)) ----
    UserApiWidget.init();

    // ----------------------------------------------------------------
    // автоматически убираем flash-сообщения через 4 секунды
    // FRONTEND (Разработчик 1 (Самира))
    // ----------------------------------------------------------------
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
