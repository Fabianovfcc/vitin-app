from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from .database import get_db_connection
from .auth import require_auth

workouts_bp = Blueprint('workouts', __name__)

@workouts_bp.route('/api/workouts', methods=['POST'])
@require_auth
def save_workout():
    data = request.get_json()
    student_id = data.get('student_id')
    student_name = data.get('student_name', '')
    workout_json = json.dumps(data)
    date = data.get('date')
    now = datetime.now().isoformat()
    
    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO workouts (student_id, workout_json, date, updated_at) VALUES (?, ?, ?, ?)',
                 (student_id, workout_json, date, now))
    conn.execute('UPDATE students SET last_workout = ? WHERE id = ?', (date, student_id))
    conn.execute('DELETE FROM workout_progress WHERE student_id = ?', (student_id,))

    conn.execute('''INSERT INTO notifications (target_role, student_id, student_name, message, type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 ('aluno', student_id, student_name, 
                  'Seu Personal atualizou sua ficha de treino!', 'workout_updated', now))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Treino enviado com sucesso!"}), 201

@workouts_bp.route('/api/workouts/history')
def get_workout_history():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id missing"}), 400
    
    conn = get_db_connection()
    history = conn.execute('''
        SELECT id, student_id, student_name, day, total_sets, completed_sets, cardio, 
               finished_at as date, finished_at as created_at 
        FROM workout_history 
        WHERE student_id = ? 
        ORDER BY finished_at DESC
    ''', (int(student_id),)).fetchall()
    conn.close()
    return jsonify([dict(h) for h in history])

@workouts_bp.route('/api/workouts/<int:student_id>')
def get_workout(student_id):
    conn = get_db_connection()
    workout = conn.execute('SELECT * FROM workouts WHERE student_id = ?', (student_id,)).fetchone()
    conn.close()
    if workout:
        data = json.loads(workout['workout_json'])
        data['updated_at'] = workout['updated_at']
        return jsonify(data)
    return jsonify({"error": "Nenhum treino encontrado"}), 404

@workouts_bp.route('/api/progress/<int:student_id>/<day>', methods=['GET', 'POST'])
def handle_progress(student_id, day):
    conn = get_db_connection()
    now = datetime.now().isoformat()
    if request.method == 'POST':
        data = request.get_json()
        completed_json = json.dumps(data.get('completedSets', {}))
        conn.execute('INSERT OR REPLACE INTO workout_progress (student_id, day, completed_sets_json, updated_at) VALUES (?, ?, ?, ?)',
                     (student_id, day, completed_json, now))
        conn.commit()
        conn.close()
        return jsonify({"status": "saved"})
    
    progress = conn.execute('SELECT * FROM workout_progress WHERE student_id = ? AND day = ?', (student_id, day)).fetchone()
    conn.close()
    return jsonify(json.loads(progress['completed_sets_json'])) if progress else jsonify({})

@workouts_bp.route('/api/workouts/finish', methods=['POST'])
def finish_workout():
    data = request.get_json()
    student_id = data.get('student_id')
    student_name = data.get('student_name', 'Aluno')
    day = data.get('day', '')
    total_sets = data.get('total_sets', 0)
    completed_sets = data.get('completed_sets', 0)
    cardio = data.get('cardio', '')
    now = datetime.now().isoformat()
    
    conn = get_db_connection()
    conn.execute('INSERT INTO workout_history (student_id, student_name, day, total_sets, completed_sets, cardio, finished_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (student_id, student_name, day, total_sets, completed_sets, cardio, now))
    
    pct = round((completed_sets / total_sets * 100)) if total_sets > 0 else 0
    msg = f'{student_name} finalizou o treino de {day.upper()} ({pct}% completo)'
    if cardio: msg += f' + Cardio: {cardio}'
    
    conn.execute('INSERT INTO notifications (target_role, student_id, student_name, message, type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                 ('professor', student_id, student_name, msg, 'workout_finished', now))
    
    today = datetime.now().strftime('%d/%m/%Y')
    conn.execute('UPDATE students SET last_workout = ?, status = ? WHERE id = ?', (today, 'active', student_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@workouts_bp.route('/api/workouts/students/all')
def get_all_students_simple():
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.id, s.name, s.access_token as token, t.name as trainer_name 
        FROM students s
        LEFT JOIN trainers t ON s.trainer_id = t.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

