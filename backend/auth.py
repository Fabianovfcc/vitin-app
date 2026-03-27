import os
from flask import request, jsonify, g
from functools import wraps
from .supabase_client import supabase

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        elif request.args.get('token'):
            token = request.args.get('token')
        
        if not token:
            return jsonify({"error": "Acesso negado. Token ausente."}), 401

        # 1. Verificar se é MASTER_TOKEN
        MASTER_TOKEN = os.getenv("MASTER_TOKEN") or os.getenv("MASTER_PASSWORD", "master_vitin_2024")
        if token == MASTER_TOKEN:
            g.user_role = 'master'
            return f(*args, **kwargs)

        # 2. Verificar se é um Aluno (access_token)
        student = supabase.table('students').select('*').eq('access_token', token).execute()
        if student.data:
            g.user_role = 'aluno'
            g.user_id = student.data[0]['id']
            g.user_data = student.data[0]
            return f(*args, **kwargs)

        # 3. Verificar se é um Professor (password como token temporário)
        trainer = supabase.table('trainers').select('*').eq('password', token).execute()
        if trainer.data:
            g.user_role = 'professor'
            g.user_id = trainer.data[0]['id']
            g.user_data = trainer.data[0]
            return f(*args, **kwargs)

        return jsonify({"error": "Token inválido ou expirado."}), 401
    return decorated
