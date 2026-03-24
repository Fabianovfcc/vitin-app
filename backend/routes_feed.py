from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from .database import get_db_connection
from .auth import require_auth
import os

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/api/feed', methods=['GET'])
def get_feed():
    conn = get_db_connection()
    now = datetime.now().isoformat()
    # Busca apenas posts que ainda não expiraram
    posts = conn.execute('''
        SELECT f.*, s.name as student_name 
        FROM feed_posts f
        JOIN students s ON f.student_id = s.id
        WHERE f.expires_at > ?
        ORDER BY f.created_at DESC
    ''', (now,)).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in posts])

@feed_bp.route('/api/feed', methods=['POST'])
@require_auth
def create_post():
    data = request.get_json()
    student_id = data.get('student_id')
    image_url = data.get('image_url')
    caption = data.get('caption', '')
    
    if not student_id or not image_url:
        return jsonify({"error": "Dados incompletos"}), 400
        
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=24)
    
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO feed_posts (student_id, image_url, caption, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_id, image_url, caption, created_at.isoformat(), expires_at.isoformat()))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "id": new_id}), 201
