import os
from flask import request, jsonify
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vitin123")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # TEMPORARIAMENTE PERMISSIVO PARA DEBUG
        return f(*args, **kwargs)
    return decorated
