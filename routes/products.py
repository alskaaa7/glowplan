# ------------------------------------------------------------
# routes/products.py - личная полка пользователя
# BACKEND (Разработчик 2 (Арина)): CRUD для UserProduct
# FRONTEND (Разработчик 1 (Самира)): шаблон products/shelf.html
# ------------------------------------------------------------

from datetime import date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import Product, UserProduct

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/shelf")
@login_required
def shelf():
    """личная полка - все открытые продукты пользователя"""
    # фильтр по статусу (из строки запроса)
    status_filter = request.args.get("status", "all")

    query = UserProduct.query.filter_by(user_id=current_user.id, is_active=True)
    user_products = query.all()

    # фильтруем на Python (продуктов немного, поэтому так проще)
    if status_filter == "expiring":
        user_products = [up for up in user_products if up.status == "expiring"]
    elif status_filter == "expired":
        user_products = [up for up in user_products if up.status == "expired"]

    return render_template(
        "products/shelf.html",
        user_products=user_products,
        status_filter=status_filter
    )

@products_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """добавить продукт на личную полку"""
    all_products = Product.query.order_by(Product.brand, Product.name).all()

    if request.method == "POST":
        product_id = request.form.get("product_id", type=int)
        opened_at_str = request.form.get("opened_at")
        notes = request.form.get("notes", "").strip()

        if not product_id or not opened_at_str:
            flash("Выберите продукт и дату открытия", "error")
            return render_template("products/add.html", all_products=all_products)

        # проверяем, что продукт уже не на полке
        existing = UserProduct.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            is_active=True
        ).first()
        if existing:
            flash("Этот продукт уже есть на вашей полке", "warning")
            return redirect(url_for("products.shelf"))

        opened_at = date.fromisoformat(opened_at_str)

        up = UserProduct(
            user_id=current_user.id,
            product_id=product_id,
            opened_at=opened_at,
            notes=notes
        )
        db.session.add(up)
        db.session.commit()
        flash("Продукт добавлен на полку!", "success")
        return redirect(url_for("products.shelf"))

    return render_template("products/add.html", all_products=all_products)


@products_bp.route("/use/<int:up_id>", methods=["POST"])
@login_required
def mark_used(up_id):
    """отметить продукт как использованный (увеличить счетчик)"""
    up = UserProduct.query.filter_by(id=up_id, user_id=current_user.id).first_or_404()
    up.uses_count += 1
    db.session.commit()
    flash(f"«{up.product.name}» - использование отмечено", "success")
    return redirect(request.referrer or url_for("products.shelf"))


@products_bp.route("/delete/<int:up_id>", methods=["POST"])
@login_required
def delete(up_id):
    """убрать продукт с полки (пометить неактивным)"""
    up = UserProduct.query.filter_by(id=up_id, user_id=current_user.id).first_or_404()
    up.is_active = False
    db.session.commit()
    flash("Продукт убран с полки", "info")
    return redirect(url_for("products.shelf"))


@products_bp.route("/catalog")
@login_required
def catalog():
    """каталог всех продуктов из общей базы"""
    category_filter = request.args.get("category", "all")
    query = Product.query

    if category_filter != "all":
        query = query.filter_by(category=category_filter)

    all_products = query.order_by(Product.brand, Product.name).all()

    categories = [
        ("all", "Все"),
        ("cleanser", "Очищение"),
        ("toner", "Тоник"),
        ("serum", "Сыворотка"),
        ("moisturizer", "Крем"),
        ("spf", "SPF"),
        ("active", "Активный уход"),
        ("oil", "Масло"),
        ("other", "Другое"),
    ]

    return render_template(
        "products/catalog.html",
        all_products=all_products,
        categories=categories,
        active_category=category_filter
    )