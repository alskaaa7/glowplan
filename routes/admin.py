# ------------------------------------------------------------
# routes/admin.py - панель администратора и бьюти-гуру
# BACKEND (Разработчик 2 (Арина)): управление продуктами, пользователями
# FRONTEND (Разработчик 1 (Самира)): шаблоны admin/
# ------------------------------------------------------------

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, Product, GuruScheme

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# декораторы доступа (Разработчик 2 (Арина)) 
def admin_required(f):
    """доступ только для администратора"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Доступ запрещён", "error")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


def guru_required(f):
    """доступ для гуру и администратора"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_guru():
            flash("Доступ запрещён", "error")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------
# панель администратора
# ------------------------------------------------------------

@admin_bp.route("/")
@login_required
@admin_required
def panel():
    """главная страница панели администратора"""
    users = User.query.order_by(User.created_at.desc()).all()
    products_count = Product.query.count()
    schemes = GuruScheme.query.order_by(GuruScheme.created_at.desc()).all()

    #рендеры самиры



@admin_bp.route("/users/role/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    """сменить роль пользователя"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")

    if new_role not in ("user", "guru", "admin"):
        flash("Неверная роль", "error")
        return redirect(url_for("admin.panel"))

    if user.id == current_user.id:
        flash("Нельзя менять собственную роль", "error")
        return redirect(url_for("admin.panel"))

    user.role = new_role
    db.session.commit()
    flash(f"Роль пользователя {user.name} изменена на «{new_role}»", "success")
    return redirect(url_for("admin.panel"))


# ------------------------------------------------------------
# управление продуктами (admin + guru)
# ------------------------------------------------------------
@admin_bp.route("/products")
@login_required
@guru_required
def products():
    """список всех продуктов в базе"""
    all_products = Product.query.order_by(Product.brand, Product.name).all()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@guru_required
def add_product():
    """добавить продукт в общую базу"""
    categories = [
        ("cleanser", "Очищение"),
        ("toner", "Тоник"),
        ("serum", "Сыворотка"),
        ("moisturizer", "Крем"),
        ("spf", "SPF"),
        ("active", "Активный уход"),
        ("oil", "Масло"),
        ("other", "Другое"),
    ]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        category = request.form.get("category", "other")
        pao_days = request.form.get("pao_days", 365, type=int)
        description = request.form.get("description", "").strip()
        ingredients = request.form.get("ingredients", "").strip()

        if not name or not brand:
            flash("Заполните название и бренд", "error")
            return render_template("admin/add_product.html", categories=categories)

        product = Product(
            name=name, brand=brand, category=category,
            pao_days=pao_days, description=description,
            ingredients=ingredients, added_by=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Продукт «{product.name}» добавлен в базу!", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/add_product.html", categories=categories)


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@guru_required
def delete_product(product_id):
    """удалить продукт из базы"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Продукт «{product.name}» удалён", "info")
    return redirect(url_for("admin.products"))


# ------------------------------------------------------------
# схемы бьюти-гуру
# ------------------------------------------------------------
@admin_bp.route("/schemes")
@login_required
@guru_required
def schemes():
    """раздел мои схемы (для гуру)"""
    my_schemes = GuruScheme.query.filter_by(guru_id=current_user.id).all()
    return render_template("admin/schemes.html", schemes=my_schemes)


@admin_bp.route("/schemes/add", methods=["GET", "POST"])
@login_required
@guru_required
def add_scheme():
    """создать новую схему ухода"""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        skin_type = request.form.get("skin_type", "all")

        if not title:
            flash("Введите название схемы", "error")
            return render_template("admin/add_scheme.html")

        scheme = GuruScheme(
            guru_id=current_user.id,
            title=title,
            description=description,
            skin_type=skin_type
        )
        db.session.add(scheme)
        db.session.commit()
        flash(f"Схема «{scheme.title}» создана!", "success")
        return redirect(url_for("admin.schemes"))

    return render_template("admin/add_scheme.html")


@admin_bp.route("/schemes/publish/<int:scheme_id>", methods=["POST"])
@login_required
@guru_required
def publish_scheme(scheme_id):
    """опубликовать / снять с публикации схему"""
    scheme = GuruScheme.query.filter_by(
        id=scheme_id, guru_id=current_user.id
    ).first_or_404()

    scheme.is_published = not scheme.is_published
    db.session.commit()

    status = "опубликована" if scheme.is_published else "снята с публикации"
    flash(f"Схема «{scheme.title}» {status}", "success")
    return redirect(url_for("admin.schemes"))


@admin_bp.route("/schemes/catalog")
@login_required
#рендеры самиры

