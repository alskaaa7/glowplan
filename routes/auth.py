# ------------------------------------------------------------
# routes/auth.py - авторизация и регистрация
# BACKEND (Разработчик 2 (Арина)): логика входа, регистрации, выхода
# ------------------------------------------------------------

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        skin_type = request.form.get("skin_type", "normal")

        # простая валидация (Разработчик 2 (Арина))
        if not name or not email or not password:
            flash("Заполните все поля", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Пароль должен быть минимум 6 символов", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует", "error")
            return render_template("auth/register.html")

        # создаем пользователя
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            skin_type=skin_type,
            role="user"
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Добро пожаловать, {user.name}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"С возвращением, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Неверный email или пароль", "error")

            
    return render_template("auth/login.html")
            



@auth_bp.route("/logout")
@login_required
def logout():
    """выход из системы"""
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("auth.login"))
