# ------------------------------------------------------------
# routes/api.py — REST API пользователей
# BACKEND (Разработчик 2 (Арина)): эндпоинты GET/POST /users,
#   валидация данных, хранение в памяти (in-memory), обработка ошибок
# ------------------------------------------------------------

import re
from flask import Blueprint, jsonify, request
from flask_login import login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ------------------------------------------------------------
# in-memory хранилище пользователей (сбрасывается при перезапуске)
# BACKEND (Разработчик 2 (Арина)): согласно заданию данные НЕ персистируются
# ------------------------------------------------------------
_users_store: list[dict] = []
_next_id: int = 1


# вспомогательные функции (Разработчик 2 (Арина)) 

def _validate_email(email: str) -> bool:
    """простая проверка формата email через регулярное выражение"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def _validate_user_payload(data: dict, require_all: bool = True) -> tuple[bool, str]:
    """
    валидация полей пользователя
    обязательные: name, email
    необязательные: age
    возвращает (is_valid, error_message)
    """
    if require_all:
        if not data.get("name") or not str(data["name"]).strip():
            return False, "Поле 'name' обязательно"
        if not data.get("email") or not str(data["email"]).strip():
            return False, "Поле 'email' обязательно"

    if data.get("email") and not _validate_email(str(data["email"])):
        return False, "Поле 'email' должно быть корректным адресом"

    if "age" in data and data["age"] is not None:
        try:
            age = int(data["age"])
            if age < 0 or age > 150:
                return False, "Поле 'age' должно быть от 0 до 150"
        except (TypeError, ValueError):
            return False, "Поле 'age' должно быть целым числом"

    return True, ""


# ------------------------------------------------------------
# GET /api/users — список всех пользователей
# BACKEND (Разработчик 2 (Арина)): возвращает массив объектов
# ------------------------------------------------------------
@api_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    """получить список всех пользователей из in-memory хранилища"""
    return jsonify({
        "status": "ok",
        "count": len(_users_store),
        "users": _users_store
    }), 200


# ------------------------------------------------------------
# GET /api/users/<id> — пользователь по идентификатору
# BACKEND (Разработчик 2 (Арина)): 404 если не найден
# ------------------------------------------------------------
@api_bp.route("/users/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id: int):
    """получить одного пользователя по id; 404 если не найден"""
    user = next((u for u in _users_store if u["id"] == user_id), None)
    if user is None:
        return jsonify({"status": "error", "message": f"Пользователь с id={user_id} не найден"}), 404
    return jsonify({"status": "ok", "user": user}), 200


# ------------------------------------------------------------
# GET /api/users/page — HTML-страница с демо-интерфейсом (для навигации)
# FRONTEND (Разработчик 1 (Самира)): шаблон api/users.html
# BACKEND (Разработчик 2 (Арина)): маршрут
# ------------------------------------------------------------
@api_bp.route("/users/page")
@login_required
def get_users_page():
    """HTML-страница с демонстрационным интерфейсом REST API пользователей"""
    from flask import render_template
    return render_template("api/users.html")


# ------------------------------------------------------------
# POST /api/users — создать нового пользователя
# BACKEND (Разработчик 2 (Арина)): валидация, уникальность email, автоинкремент id
# ------------------------------------------------------------
@api_bp.route("/users", methods=["POST"])
@login_required
def create_user():
    """
    создать нового пользователя
    обязательные поля: name, email
    необязательные: age
    возвращает созданный объект с автоматически присвоенным id
    """
    global _next_id

    # парсим JSON-тело запроса
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Тело запроса должно быть JSON"}), 400

    # валидация полей
    is_valid, error_msg = _validate_user_payload(data, require_all=True)
    if not is_valid:
        return jsonify({"status": "error", "message": error_msg}), 422

    # проверяем уникальность email
    email_lower = str(data["email"]).strip().lower()
    if any(u["email"] == email_lower for u in _users_store):
        return jsonify({"status": "error", "message": "Пользователь с таким email уже существует"}), 409

    # создаём объект пользователя
    new_user = {
        "id":    _next_id,
        "name":  str(data["name"]).strip(),
        "email": email_lower,
        "age":   int(data["age"]) if data.get("age") is not None else None,
    }
    _users_store.append(new_user)
    _next_id += 1

    return jsonify({"status": "ok", "user": new_user}), 201
