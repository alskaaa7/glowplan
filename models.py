# ------------------------------------------------------------
# models.py - модели базы данных (SQLAlchemy ORM)
# BACKEND (Разработчик 2 (Арина)): все модели, связи, бизнес-логика
# ------------------------------------------------------------

from datetime import date, timedelta
from flask_login import UserMixin
from extensions import db, login_manager


# загрузчик пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------------------------------------
# модель пользователя
# ------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    skin_type = db.Column(db.String(40), default="normal") # normal, dry, oily, combo
    role = db.Column(db.String(20), default="user") # user, guru, admin
    created_at = db.Column(db.Date, default=date.today)

    # связи
    user_products = db.relationship("UserProduct", backref="owner", lazy=True, cascade="all, delete-orphan")
    routines = db.relationship("Routine", backref="owner", lazy=True, cascade="all, delete-orphan")
    checklist_logs = db.relationship("ChecklistLog", backref="owner", lazy=True, cascade="all, delete-orphan")
    guru_schemes = db.relationship("GuruScheme", backref="author", lazy=True)

    def is_admin(self):
        return self.role == "admin"

    def is_guru(self):
        return self.role in ("guru", "admin")

    def __repr__(self):
        return f"<User {self.email}>"


# ------------------------------------------------------------
# общая база продуктов (заполняет admin / guru)
# ------------------------------------------------------------
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(80), nullable=False)
    # категории: cleanser, toner, serum, moisturizer, spf, active, oil, other
    category = db.Column(db.String(40), nullable=False)
    pao_days = db.Column(db.Integer, nullable=False) # срок после вскрытия в днях
    description = db.Column(db.Text, default="")
    # ключевые ингредиенты через запятую: retinol, aha, bha, vitamin_c, niacinamide
    ingredients = db.Column(db.String(200), default="")
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Product {self.brand} — {self.name}>"


# ------------------------------------------------------------
# личная полка пользователя (открытые продукты)
# ------------------------------------------------------------
class UserProduct(db.Model):
    __tablename__ = "user_products"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    opened_at = db.Column(db.Date, nullable=False, default=date.today)
    uses_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(200), default="")

    product = db.relationship("Product", lazy=True)

    # вычисляемые свойства (бизнес-логика)
    @property
    def expires_at(self):
        """дата истечения = дата открытия + PAO"""
        return self.opened_at + timedelta(days=self.product.pao_days)

    @property
    def days_left(self):
        """сколько дней осталось до истечения"""
        return (self.expires_at - date.today()).days

    @property
    def status(self):
        """статус продукта: active / expiring / expired"""
        if self.days_left < 0:
            return "expired"
        elif self.days_left <= 14:
            return "expiring"
        return "active"

    def __repr__(self):
        return f"<UserProduct user={self.user_id} product={self.product_id}>"


# ------------------------------------------------------------
# рутина: слот = день недели + время суток
# ------------------------------------------------------------
class Routine(db.Model):
    __tablename__ = "routines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # 0 = Понедельник <-> 6 = Воскресенье
    day_of_week = db.Column(db.Integer, nullable=False)
    time_of_day = db.Column(db.String(10), nullable=False) # morning / evening

    steps = db.relationship("RoutineStep", backref="routine", lazy=True,
                             cascade="all, delete-orphan", order_by="RoutineStep.step_order")


# ------------------------------------------------------------
# шаг внутри рутины
# ------------------------------------------------------------
class RoutineStep(db.Model):
    __tablename__ = "routine_steps"

    id = db.Column(db.Integer, primary_key=True)
    routine_id = db.Column(db.Integer, db.ForeignKey("routines.id"), nullable=False)
    user_product_id = db.Column(db.Integer, db.ForeignKey("user_products.id"), nullable=False)
    step_order = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(200), default="")

    user_product = db.relationship("UserProduct", lazy=True)


# ------------------------------------------------------------
# журнал выполнения чек-листа перед сном
# ------------------------------------------------------------
class ChecklistLog(db.Model):
    __tablename__ = "checklist_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    # JSON-строка: ["makeup_removal", "teeth", "lips", "hands", "night_care"]
    completed_items = db.Column(db.Text, default="[]")


# ------------------------------------------------------------
# схемы бьюти-гуру
# ------------------------------------------------------------
class GuruScheme(db.Model):
    __tablename__ = "guru_schemes"

    id = db.Column(db.Integer, primary_key=True)
    guru_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    skin_type = db.Column(db.String(40), default="all") # для какого типа кожи
    is_published = db.Column(db.Boolean, default=False)
    imports_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Date, default=date.today)
