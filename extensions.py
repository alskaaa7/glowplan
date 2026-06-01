# ------------------------------------------------------------
# extensions.py — расширения Flask (db, login_manager)
# BACKEND (Разработчик 3 (Даша)): вынесено сюда чтобы избежать циклического импорта между app.py и models.py
# ------------------------------------------------------------

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()