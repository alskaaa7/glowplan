# ------------------------------------------------------------
# routes/routine.py - конструктор рутины
# BACKEND (Разработчик 2 (Арина)): CRUD для Routine и RoutineStep
# FRONTEND (Разработчик 1 (Самира)): шаблон routine/index.html
# ------------------------------------------------------------

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import Routine, RoutineStep, UserProduct

routine_bp = Blueprint("routine", __name__, url_prefix="/routine")

DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


@routine_bp.route("/")
@login_required
def index():
    """конструктор рутины - таблица по дням недели"""
    # группируем рутину по дням и времени
    schedule = {}
    for day in range(7):
        schedule[day] = {
            "name": DAYS_RU[day],
            "morning": Routine.query.filter_by(
                user_id=current_user.id, day_of_week=day, time_of_day="morning"
            ).first(),
            "evening": Routine.query.filter_by(
                user_id=current_user.id, day_of_week=day, time_of_day="evening"
            ).first(),
        }

    return render_template("routine/index.html", schedule=schedule)


@routine_bp.route("/edit/<int:day>/<time_of_day>", methods=["GET", "POST"])
@login_required
#рендеры самиры для рутины

    # находим или создаем слот
    routine = Routine.query.filter_by(
        user_id=current_user.id,
        day_of_week=day,
        time_of_day=time_of_day
    ).first()

    if not routine:
        routine = Routine(
            user_id=current_user.id,
            day_of_week=day,
            time_of_day=time_of_day
        )
        db.session.add(routine)
        db.session.commit()

    # продукты на полке пользователя (доступны для добавления в рутину)
    user_products = UserProduct.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()

    if request.method == "POST":
        # получаем упорядоченный список product_id из формы
        selected_ids = request.form.getlist("user_product_ids")

        # удаляем старые шаги и создаем новые
        RoutineStep.query.filter_by(routine_id=routine.id).delete()

        for order, up_id in enumerate(selected_ids):
            step = RoutineStep(
                routine_id=routine.id,
                user_product_id=int(up_id),
                step_order=order
            )
            db.session.add(step)

        db.session.commit()
        flash(f"Рутина на {DAYS_RU[day]} ({_time_label(time_of_day)}) сохранена!", "success")
        return redirect(url_for("routine.index"))

    #рендеры самиры



#роуты самиры


def _time_label(time_of_day):
    return "Утро" if time_of_day == "morning" else "Вечер"
