from flask import Blueprint, jsonify, request
from datetime import datetime
from .database import get_db_connection
from .auth import require_auth

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/exercises', methods=['GET', 'POST'])
@require_auth
def handle_exercises():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        if 'id' in data:
            conn.execute("UPDATE exercises SET name=?, category=?, image=? WHERE id=?", 
                         (data['name'], data['category'], data['image'], data['id']))
        else:
            cursor = conn.execute("INSERT INTO exercises (name, category, image) VALUES (?, ?, ?)", 
                         (data['name'], data['category'], data['image']))
            data['id'] = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify(data)
    
    exercises = conn.execute('SELECT * FROM exercises').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in exercises])

@admin_bp.route('/api/notifications/<role>')
def get_notifications(role):
    conn = get_db_connection()
    student_id = request.args.get('student_id')
    if role == 'aluno' and student_id:
        notifs = conn.execute('SELECT * FROM notifications WHERE target_role = ? AND student_id = ? ORDER BY created_at DESC LIMIT 20', (role, student_id)).fetchall()
    else:
        notifs = conn.execute('SELECT * FROM notifications WHERE target_role = ? ORDER BY created_at DESC LIMIT 20', (role,)).fetchall()
    conn.close()
    return jsonify([dict(n) for n in notifs])

@admin_bp.route('/api/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    data = request.get_json()
    role = data.get('role', '')
    student_id = data.get('student_id')
    conn = get_db_connection()
    if role == 'aluno' and student_id:
        conn.execute('UPDATE notifications SET is_read = 1 WHERE target_role = ? AND student_id = ?', (role, student_id))
    elif role == 'professor':
        conn.execute('UPDATE notifications SET is_read = 1 WHERE target_role = ?', (role,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@admin_bp.route('/api/notifications/unread-count/<role>')
def unread_count(role):
    conn = get_db_connection()
    student_id = request.args.get('student_id')
    if role == 'aluno' and student_id:
        count = conn.execute('SELECT COUNT(*) FROM notifications WHERE target_role = ? AND student_id = ? AND is_read = 0', (role, student_id)).fetchone()[0]
    else:
        count = conn.execute('SELECT COUNT(*) FROM notifications WHERE target_role = ? AND is_read = 0', (role,)).fetchone()[0]
    conn.close()
    return jsonify({"count": count})

@admin_bp.route('/api/challenges/active', methods=['GET', 'POST', 'DELETE'])
def handle_active_challenge():
    # Nota: require_auth é chamado internamente para POST/DELETE
    if request.method in ['POST', 'DELETE']:
        # Simples bypass para usar o decorador isoladamente se necessário, 
        # mas aqui vamos apenas replicar a lógica ou importar require_auth
        @require_auth
        def protected(): pass
        res = protected()
        if res: return res

    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        now = datetime.now().isoformat()
        conn.execute('UPDATE challenges SET active = 0')
        if data.get('title') and data.get('description'):
            conn.execute('INSERT INTO challenges (title, description, active, created_at) VALUES (?, ?, 1, ?)', (data['title'], data['description'], now))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    elif request.method == 'DELETE':
        conn.execute('UPDATE challenges SET active = 0')
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})
    
    challenge = conn.execute('SELECT * FROM challenges WHERE active = 1 ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return jsonify(dict(challenge)) if challenge else (jsonify({"active": False}), 404)

@admin_bp.route('/api/history/<int:student_id>')
def get_history(student_id):
    conn = get_db_connection()
    history = conn.execute('SELECT * FROM workout_history WHERE student_id = ? ORDER BY finished_at DESC LIMIT 30', (student_id,)).fetchall()
    conn.close()
    return jsonify([dict(h) for h in history])

@admin_bp.route('/api/history/recent')
def recent_history():
    conn = get_db_connection()
    history = conn.execute('SELECT * FROM workout_history ORDER BY finished_at DESC LIMIT 20').fetchall()
    conn.close()
    return jsonify([dict(h) for h in history])
