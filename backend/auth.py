import os
from flask import request, jsonify
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vitin123")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {ADMIN_PASSWORD}":
            return jsonify({"error": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated
