# ------------------------------------------------------------
# app.py — точка входа Flask-приложения
# BACKEND (Разработчик 2 (Арина)): инициализация Flask, SQLAlchemy, Flask-Login,
#   регистрация маршрутов, в т.ч. нового api_bp
# ------------------------------------------------------------

from flask import Flask
from extensions import db, login_manager
import os



def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-fallback-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///glowplan.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Пожалуйста, войдите в систему"

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.products import products_bp
    from routes.routine import routine_bp
    from routes.admin import admin_bp
    from routes.api import api_bp          # NEW — REST API пользователей

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(routine_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)         # NEW

    with app.app_context():
        import models  # noqa: F401
        db.create_all()
        _seed_default_products()

    return app


def _seed_default_products():
    from models import Product
    if Product.query.count() > 0:
        return
    defaults = [
        Product(name="Gentle Foam Cleanser", brand="CeraVe", category="cleanser",
                pao_days=365, ingredients="ceramides", description="Мягкая пенка для умывания"),
        Product(name="Hydrating Toner", brand="Klairs", category="toner",
                pao_days=365, ingredients="hyaluronic_acid", description="Увлажняющий тоник"),
        Product(name="Vitamin C Serum 15%", brand="Paula's Choice", category="serum",
                pao_days=90, ingredients="vitamin_c", description="Сыворотка с витамином C — хранить в холоде"),
        Product(name="Retinol 0.3%", brand="The Ordinary", category="active",
                pao_days=180, ingredients="retinol", description="Ретинол — только вечером"),
        Product(name="AHA 30% + BHA 2%", brand="The Ordinary", category="active",
                pao_days=365, ingredients="aha,bha", description="Кислотный пилинг — 1–2 раза в неделю"),
        Product(name="Moisturizer SPF 30", brand="La Roche-Posay", category="spf",
                pao_days=365, ingredients="spf", description="Увлажняющий крем с SPF — утром обязательно"),
        Product(name="Barrier Cream", brand="Dr.Jart+", category="moisturizer",
                pao_days=365, ingredients="ceramides,niacinamide", description="Восстанавливающий крем"),
        Product(name="Niacinamide 10%", brand="The Ordinary", category="serum",
                pao_days=365, ingredients="niacinamide", description="Сыворотка с ниацинамидом"),
        Product(name="Cleansing Oil", brand="DHC", category="oil",
                pao_days=365, ingredients="", description="Гидрофильное масло для демакияжа"),
    ]
    db.session.add_all(defaults)
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
