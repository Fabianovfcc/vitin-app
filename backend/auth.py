import os
from flask import request, jsonify
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vitin123")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Para alunos, verificamos o token ou ID no cabeçalho ou storage
        # Por enquanto, permitimos se o token for enviado via query ou header
        token = request.headers.get('Authorization') or request.args.get('token')
        
        # Se for uma rota de aluno, permitimos por enquanto via access_token
        # mas no futuro validaremos sessão persistente.
        if not token:
            return jsonify({"error": "Acesso negado. Faça login."}), 401
            
        return f(*args, **kwargs)
    return decorated
