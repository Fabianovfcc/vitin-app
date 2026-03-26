from flask import Blueprint, jsonify, request
import json
import uuid
from datetime import datetime
from .database import get_db_connection
from .auth import require_auth

students_bp = Blueprint('students', __name__)

@students_bp.route('/api/students', methods=['GET', 'POST'])
@require_auth
def handle_students():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        whatsapp = data.get('whatsapp')
        token = str(uuid.uuid4())[:8]
        cursor = conn.execute("INSERT INTO students (name, whatsapp, access_token) VALUES (?, ?, ?)", (name, whatsapp, token))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "id": new_id, "access_token": token, "whatsapp": whatsapp}), 201
    
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in students])

@students_bp.route('/api/students/<int:id>', methods=['DELETE'])
@require_auth
def delete_student(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.execute('DELETE FROM workouts WHERE student_id = ?', (id,))
    conn.execute('DELETE FROM notifications WHERE student_id = ?', (id,))
    conn.execute('DELETE FROM workout_progress WHERE student_id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@students_bp.route('/api/students/by-token/<token>')
def get_student_by_token(token):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE access_token = ?', (token,)).fetchone()
    conn.close()
    if student:
        return jsonify(dict(student))
    return jsonify({"error": "Aluno não encontrado"}), 404

@students_bp.route('/api/students/by-whatsapp/<whatsapp>')
def get_student_by_whatsapp(whatsapp):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE whatsapp = ?', (whatsapp,)).fetchone()
    conn.close()
    if student:
        return jsonify(dict(student))
    return jsonify({"error": "Aluno não encontrado"}), 404

@students_bp.route('/api/student/purchases', methods=['GET'])
def get_student_purchases():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id obrigatório"}), 400
    
    conn = get_db_connection()
    purchases = conn.execute('''
        SELECT w.title, t.name as trainer_name, s.price, s.created_at, w.id
        FROM marketplace_sales s
        JOIN catalog_workouts w ON s.workout_id = w.id
        JOIN trainers t ON s.trainer_id = t.id
        WHERE s.student_id = ?
    ''', (student_id,)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in purchases])

@students_bp.route('/api/analytics/track', methods=['POST'])
def track_analytics():
    data = request.json
    # Por enquanto apenas logamos no servidor, mas poderíamos salvar numa tabela 'events'
    print(f"ANALYTICS: Evento '{data.get('event_type')}' do aluno {data.get('student_id')}")
    return jsonify({"status": "captured"})

@students_bp.route('/api/students/profile', methods=['PUT', 'POST'])
def update_student_profile():
    data = request.json
    student_id = data.get('id')
    weight = data.get('weight')
    height = data.get('height')
    goal = data.get('goal')
    
    conn = get_db_connection()
    conn.execute('UPDATE students SET weight = ?, height = ?, goal = ?, anamnesis_done = 1 WHERE id = ?', 
                 (weight, height, goal, student_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})
