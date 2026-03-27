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
            g.user_id = 0  # Master ID universal
            return f(*args, **kwargs)

        # 2. Verificar se é um Aluno (access_token)
        student = supabase.table('students').select('*').eq('access_token', token).execute()
        if student.data:
            g.user_role = 'aluno'
            g.user_id = student.data[0]['id']
            g.user_data = student.data[0]
            return f(*args, **kwargs)

        # 3. Verificar se é um Professor (Formato: whatsapp:senha ou token único)
        # Tenta splitar caso venha no formato whatsapp:senha
        if ":" in token:
            whatsapp, password = token.split(":", 1)
            trainer = supabase.table('trainers').select('*').eq('whatsapp', whatsapp).eq('password', password).execute()
        else:
            # Fallback para compatibilidade ou se o token for apenas a senha (antigo, mas vamos restringir)
            trainer = supabase.table('trainers').select('*').eq('password', token).execute()
            
        if trainer.data:
            # Se houver mais de um com a mesma senha e não usamos WhatsApp, avisar (ou apenas pegar o primeiro)
            # Idealmente, o login sempre enviará whatsapp:senha a partir de agora
            g.user_role = 'professor'
            g.user_id = trainer.data[0]['id']
            g.user_data = trainer.data[0]
            return f(*args, **kwargs)

        return jsonify({"error": "Sua sessão expirou ou a senha está incorreta."}), 401
    return decorated
