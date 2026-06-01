# ------------------------------------------------------------
# routes/main.py - главная страница, дашборд, профиль, чек-лист
# BACKEND (Разработчик 2 (Арина)): логика дашборда, уведомлений
# FRONTEND (Разработчик 1 (Самира)): шаблоны dashboard.html, profile.html
# ------------------------------------------------------------

import json
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Routine, RoutineStep, UserProduct, ChecklistLog

main_bp = Blueprint("main", __name__)

# дни недели на русском (Разработчик 2 (Арина))
DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# пункты чек-листа перед сном (Разработчик 2 (Арина))
CHECKLIST_ITEMS = [
    ("makeup_removal", "Демакияж"),
    ("teeth", "Чистка зубов"),
    ("lips", "Увлажнение губ"),
    ("hands", "Крем для рук"),
    ("night_care", "Ночной уход"),
]

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    дашборд «Сегодня»
    BACKEND (Разработчик 2 (Арина)): собирает данные рутины, уведомления
    FRONTEND (Разработчик 1 (Самира)): шаблон dashboard.html
    """
    today = date.today()
    weekday = today.weekday()  # 0 = понедельник

    # утренняя и вечерняя рутина на сегодня
    morning_routine = Routine.query.filter_by(
        user_id=current_user.id,
        day_of_week=weekday,
        time_of_day="morning"
    ).first()

    evening_routine = Routine.query.filter_by(
        user_id=current_user.id,
        day_of_week=weekday,
        time_of_day="evening"
    ).first()

    # уведомления - собираем список предупреждений (Разработчик 2 (Арина))
    notifications = get_notifications(current_user)

    # чек-лист — был ли уже заполнен сегодня
    today_log = ChecklistLog.query.filter_by(
        user_id=current_user.id,
        log_date=today
    ).first()

    completed_items = json.loads(today_log.completed_items) if today_log else []

    
    return render_template(
        "main/dashboard.html",
        morning_routine=morning_routine,
        evening_routine=evening_routine,
        notifications=notifications,
        checklist_items=CHECKLIST_ITEMS,
        completed_items=completed_items,
        today_name=DAYS_RU[weekday],
        today=today,
    )



def get_notifications(user):
    """
    логика умных уведомлений
    BACKEND (Разработчик 2 (Арина)): проверяет продукты и возвращает список предупреждений
    """
    notifications = []

    # проверяем все активные продукты пользователя
    user_products = UserProduct.query.filter_by(
        user_id=user.id, is_active=True
    ).all()

    for up in user_products:
        # 1. если скоро истекает срок годности
        if up.status == "expired":
            notifications.append({
                "type": "danger",
                "text": f"Срок годности «{up.product.name}» истёк! Пора выбросить."
            })
        elif up.status == "expiring":
            notifications.append({
                "type": "warning",
                "text": f"«{up.product.name}» истекает через {up.days_left} дн. - используй активнее!"
            })

        # 2. витамин C давно не использовался (>3 дней без использования - окисляется)
        if "vitamin_c" in (up.product.ingredients or ""):
            if up.uses_count == 0:
                notifications.append({
                    "type": "info",
                    "text": f"«{up.product.name}» ещё не использовалась - добавь в рутину для поддержания здорового тона лица!"
                })

    # 3. проверяем конфликты в рутине на сегодня
    conflict_notes = check_ingredient_conflicts(user)
    notifications.extend(conflict_notes)

    return notifications


def check_ingredient_conflicts(user):
    """
    проверка конфликтов ингредиентов в расписании
    BACKEND (Разработчик 2 (Арина)): алгоритм несовместимости
    """
    conflicts = []
    today = date.today()
    weekday = today.weekday()
    tomorrow_weekday = (weekday + 1) % 7

    # собираем ингредиенты вечерней рутины сегодня
    evening = Routine.query.filter_by(
        user_id=user.id, day_of_week=weekday, time_of_day="evening"
    ).first()

    evening_ingredients = []
    has_retinol = False
    has_acids = False

    if evening:
        for step in evening.steps:
            ings = (step.user_product.product.ingredients or "").split(",")
            evening_ingredients.extend(ings)
            if "retinol" in ings:
                has_retinol = True
            if "aha" in ings or "bha" in ings:
                has_acids = True

    # предупреждение: ретинол + кислоты в один вечер
    if has_retinol and has_acids:
        conflicts.append({
            "type": "danger",
            "text": "Предупреждение! Ретинол и кислоты нельзя использовать в один вечер."
        })

    # напоминание: после пилинга завтра утром нужен SPF
    if has_acids:
        morning_tomorrow = Routine.query.filter_by(
            user_id=user.id, day_of_week=tomorrow_weekday, time_of_day="morning"
        ).first()

        has_spf_tomorrow = False
        if morning_tomorrow:
            for step in morning_tomorrow.steps:
                if "spf" in (step.user_product.product.ingredients or ""):
                    has_spf_tomorrow = True

        conflicts.append({
            "type": "warning" if has_spf_tomorrow else "danger",
            "text": "Сегодня день пилинга! Завтра утром обязателен SPF." +
            ("Уже есть в рутине." if has_spf_tomorrow else "Добавь SPF в утреннюю рутину!")
        })

    # напоминание про ретинол
    if has_retinol:
        conflicts.append({
            "type": "info",
            "text": "Вечер ретинола! Нанеси на сухую кожу после умывания."
        })

    return conflicts


@main_bp.route("/checklist", methods=["POST"])
@login_required
def save_checklist():
    """сохранение чек-листа перед сном (BACKEND - Разработчик 2 (Арина))"""
    today = date.today()
    completed = request.form.getlist("items")

    log = ChecklistLog.query.filter_by(
        user_id=current_user.id, log_date=today
    ).first()

    if log:
        log.completed_items = json.dumps(completed)
    else:
        log = ChecklistLog(
            user_id=current_user.id,
            log_date=today,
            completed_items=json.dumps(completed)
        )
        db.session.add(log)

    db.session.commit()
    flash("Чек-лист сохранён. Доброй ночи!", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """страница профиля пользователя"""
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.skin_type = request.form.get("skin_type", current_user.skin_type)

        new_password = request.form.get("new_password", "")
        if new_password and len(new_password) >= 6:
            current_user.password_hash = generate_password_hash(new_password)
            flash("Пароль обновлён", "success")

        db.session.commit()
        flash("Профиль сохранён", "success")
        return redirect(url_for("main.profile"))

    # статистика чек-листа за последние 7 дней
    from datetime import timedelta
    week_logs = ChecklistLog.query.filter(
        ChecklistLog.user_id == current_user.id,
        ChecklistLog.log_date >= date.today() - timedelta(days=6)
    ).all()

    checklist_stats = len(week_logs)  # сколько дней из 7 заполнен чек-лист

    return render_template(
        "main/profile.html",
        checklist_stats=checklist_stats,
        skin_types=["normal", "dry", "oily", "combo"]
    )
