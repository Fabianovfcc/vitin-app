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
        token = str(uuid.uuid4())[:8]
        cursor = conn.execute("INSERT INTO students (name, access_token) VALUES (?, ?)", (name, token))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "id": new_id, "access_token": token}), 201
    
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
