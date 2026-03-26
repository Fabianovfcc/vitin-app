from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from .supabase_client import supabase
import base64
import time

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/api/feed', methods=['GET'])
def get_feed():
    student_id = request.args.get('student_id')
    now = datetime.now().isoformat()
    
    if student_id:
        # Busca dados do aluno para filtrar o feed
        student_result = supabase.table('students').select('trainer_id, gym_id').eq('id', student_id).execute()
        student = student_result.data[0] if student_result.data else None
    else:
        student = None
    
    if student:
        trainer_id = student.get('trainer_id')
        gym_id = student.get('gym_id')
        
        # Buscar todos os posts não expirados e filtrar no Python
        # (Supabase REST não suporta OR complexo com múltiplos campos)
        result = supabase.table('feed_posts').select(
            '*, students(name)'
        ).gt('expires_at', now).order('created_at', desc=True).execute()
        
        posts = []
        for p in result.data:
            vis = p.get('visibility', 'public')
            # Lógica de visibilidade
            if (vis == 'public' 
                or (vis == 'gym' and p.get('gym_id') == gym_id)
                or (vis == 'trainer' and p.get('trainer_id') == trainer_id)
                or str(p.get('student_id')) == str(student_id)):
                # Flatten student name
                p['student_name'] = p.get('students', {}).get('name', p.get('student_name', ''))
                if 'students' in p:
                    del p['students']
                posts.append(p)
        return jsonify(posts)
    else:
        result = supabase.table('feed_posts').select(
            '*, students(name)'
        ).eq('visibility', 'public').gt('expires_at', now).order('created_at', desc=True).execute()
        
        posts = []
        for p in result.data:
            p['student_name'] = p.get('students', {}).get('name', p.get('student_name', ''))
            if 'students' in p:
                del p['students']
            posts.append(p)
        return jsonify(posts)

@feed_bp.route('/api/feed', methods=['POST'])
def create_post():
    data = request.get_json()
    student_id = data.get('student_id')
    image_data = data.get('image_url') or data.get('image_base64')
    caption = data.get('caption', '')
    
    if not student_id or not image_data:
        return jsonify({"error": "Dados incompletos"}), 400
    
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=24)
    visibility = data.get('visibility', 'public')
    
    # Upload para Supabase Storage se for Base64
    image_url = image_data
    if image_data and image_data.startswith('data:'):
        try:
            # Extrair bytes do Base64
            base64_str = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(base64_str)
            filename = f"feed/{student_id}_{int(time.time())}.jpg"
            
            supabase.storage.from_('feed-imagens').upload(
                filename, image_bytes, 
                {"content-type": "image/jpeg"}
            )
            
            # URL pública
            image_url = supabase.storage.from_('feed-imagens').get_public_url(filename)
        except Exception as e:
            print(f"ERRO UPLOAD STORAGE: {e}")
            # Fallback: salva o base64 direto (não ideal, mas funciona)
            image_url = image_data
    
    # Pega trainer_id e gym_id do aluno
    student_result = supabase.table('students').select('trainer_id, gym_id').eq('id', student_id).execute()
    student = student_result.data[0] if student_result.data else {}
    
    result = supabase.table('feed_posts').insert({
        'student_id': student_id,
        'image_url': image_url,
        'caption': caption,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'visibility': visibility,
        'trainer_id': student.get('trainer_id'),
        'gym_id': student.get('gym_id')
    }).execute()
    
    new_id = result.data[0]['id'] if result.data else None
    return jsonify({"status": "success", "id": new_id}), 201
