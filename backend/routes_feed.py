from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from .database import get_db_connection
from .auth import require_auth
import os

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/api/feed', methods=['GET'])
def get_feed():
    student_id = request.args.get('student_id')
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    # Busca dados do aluno para filtrar o feed
    student = None
    if student_id:
        student = conn.execute('SELECT trainer_id, gym_id FROM students WHERE id = ?', (student_id,)).fetchone()
    
    if student:
        # Filtro: Públicos + Mesma Academia + Mesmo Treinador
        posts = conn.execute('''
            SELECT f.*, s.name as student_name 
            FROM feed_posts f
            JOIN students s ON f.student_id = s.id
            WHERE f.expires_at > ?
            AND (
                f.visibility = 'public' 
                OR (f.visibility = 'gym' AND f.gym_id = ?)
                OR (f.visibility = 'trainer' AND f.trainer_id = ?)
                OR f.student_id = ?
            )
            ORDER BY f.created_at DESC
        ''', (now, student['gym_id'], student['trainer_id'], student_id)).fetchall()
    else:
        # Fallback para posts públicos se não houver contexto de aluno
        posts = conn.execute('''
            SELECT f.*, s.name as student_name 
            FROM feed_posts f
            JOIN students s ON f.student_id = s.id
            WHERE f.expires_at > ? AND f.visibility = 'public'
            ORDER BY f.created_at DESC
        ''', (now,)).fetchall()
        
    conn.close()
    return jsonify([dict(ix) for ix in posts])

@feed_bp.route('/api/feed', methods=['POST'])
@require_auth
def create_post():
    data = request.get_json()
    student_id = data.get('student_id')
    image_url = data.get('image_url') or data.get('image_base64')
    caption = data.get('caption', '')
    
    if not student_id or not image_url:
        return jsonify({"error": "Dados incompletos"}), 400
        
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=24)
    visibility = data.get('visibility', 'public')
    
    conn = get_db_connection()
    # Pega trainer_id e gym_id do aluno no momento da postagem
    student = conn.execute('SELECT trainer_id, gym_id FROM students WHERE id = ?', (student_id,)).fetchone()
    trainer_id = student['trainer_id'] if student else None
    gym_id = student['gym_id'] if student else None

    cursor = conn.execute('''
        INSERT INTO feed_posts (student_id, image_url, caption, created_at, expires_at, visibility, trainer_id, gym_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, image_url, caption, created_at.isoformat(), expires_at.isoformat(), visibility, trainer_id, gym_id))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "id": new_id}), 201
