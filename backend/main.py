import sqlite3
import json
from flask import Flask, send_from_directory, jsonify, request
from datetime import datetime
import os

app = Flask(__name__, static_folder='../frontend')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'vitin.db')

os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Alunos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            last_workout TEXT,
            status TEXT DEFAULT 'active',
            access_token TEXT UNIQUE
        )
    ''')
    
    # Tabela de Exercícios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            image TEXT NOT NULL
        )
    ''')
    
    # Tabela de Treinos (Fichas enviadas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            student_id INTEGER PRIMARY KEY,
            workout_json TEXT NOT NULL,
            date TEXT NOT NULL,
            updated_at TEXT
        )
    ''')

    # Tabela de Notificações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_role TEXT NOT NULL,
            student_id INTEGER,
            student_name TEXT,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Tabela de Desafios Globais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    ''')

    # Tabela de Progresso do Treino (séries marcadas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_progress (
            student_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            completed_sets_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (student_id, day)
        )
    ''')

    # Tabela de Histórico de Treinos Finalizados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            student_name TEXT,
            day TEXT NOT NULL,
            total_sets INTEGER,
            completed_sets INTEGER,
            cardio TEXT,
            finished_at TEXT NOT NULL
        )
    ''')

    # Adicionar coluna access_token se não existir (migração suave)
    try:
        cursor.execute("SELECT access_token FROM students LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE students ADD COLUMN access_token TEXT UNIQUE")

    # Adicionar coluna updated_at se não existir
    try:
        cursor.execute("SELECT updated_at FROM workouts LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE workouts ADD COLUMN updated_at TEXT")

    # Inserir alunos iniciais se a tabela estiver vazia
    cursor.execute('SELECT COUNT(*) FROM students')
    if cursor.fetchone()[0] == 0:
        import uuid
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('João Silva', '2026-03-09', 'active', str(uuid.uuid4())[:8]))
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('Maria Oliveira', '2026-03-10', 'active', str(uuid.uuid4())[:8]))
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('Pedro Santos', '2026-03-05', 'late', str(uuid.uuid4())[:8]))
    else:
        # Gerar tokens para alunos existentes que não têm
        import uuid
        students_without_token = cursor.execute("SELECT id FROM students WHERE access_token IS NULL").fetchall()
        for s in students_without_token:
            cursor.execute("UPDATE students SET access_token = ? WHERE id = ?", (str(uuid.uuid4())[:8], s['id']))

    # Inserir exercícios iniciais se estiver vazia
    cursor.execute('SELECT COUNT(*) FROM exercises')
    if cursor.fetchone()[0] == 0:
        all_categories = {
            "Peito": ["Supino Reto", "Supino Inclinado", "Supino Declinado", "Crucifixo", "Crossover", "Flexão de Braço"],
            "Costas": ["Puxada Frente", "Remada Curvada", "Remada Unilateral", "Puxada Atrás", "Pullover", "Remada Cavalinho"],
            "Ombros": ["Elevação Lateral", "Desenvolvimento Máquina", "Desenvolvimento Halteres", "Elevação Frontal", "Crucifixo Invertido"],
            "Bíceps": ["Rosca Direta", "Rosca Alternada", "Rosca Scott", "Rosca Martelo", "Rosca Concentrada"],
            "Tríceps": ["Tríceps Pulley", "Tríceps Testa", "Tríceps Francês", "Mergulho", "Tríceps Coice"],
            "Pernas": ["Agachamento Livre", "Leg Press", "Cadeira Extensora", "Mesa Flexora", "Agachamento Hack", "Passada", "Stiff"],
            "Glúteos": ["Hip Thrust", "Abdução de Quadril", "Glúteo Máquina"],
            "Panturrilha": ["Panturrilha em Pé", "Panturrilha Sentado", "Panturrilha no Leg Press"],
            "Abdômen": ["Abdominal Supra", "Abdominal Infra", "Prancha", "Abdominal Oblíquo", "Roda Abdominal"],
            "Trapézio": ["Encolhimento Barra", "Encolhimento Halteres"],
            "Antebraço": ["Rosca Punho", "Rosca Inversa"]
        }
        for cat, names in all_categories.items():
            for name in names:
                img = "icon:" + cat
                if name == "Supino Reto": img = "/assets/exercises/chest_press.png"
                if name == "Puxada Frente": img = "/assets/exercises/lat_pulldown.png"
                if name == "Elevação Lateral": img = "/assets/exercises/lateral_raise.png"
                if name == "Agachamento Livre": img = "/assets/exercises/squat.png"
                cursor.execute("INSERT INTO exercises (name, category, image) VALUES (?, ?, ?)", (name, cat, img))

    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────
# ROTAS DE PÁGINAS
# ────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/aluno')
def aluno():
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/aluno/<token>')
def aluno_direto(token):
    """Link direto para o aluno acessar sem selecionar nome."""
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# ────────────────────────────────────────
# API DE ALUNOS
# ────────────────────────────────────────
@app.route('/api/students', methods=['GET', 'POST'])
def handle_students():
    conn = get_db_connection()
    if request.method == 'POST':
        import uuid
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

@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.execute('DELETE FROM workouts WHERE student_id = ?', (id,))
    conn.execute('DELETE FROM notifications WHERE student_id = ?', (id,))
    conn.execute('DELETE FROM workout_progress WHERE student_id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/students/by-token/<token>')
def get_student_by_token(token):
    """Busca aluno pelo token de acesso (link direto)."""
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE access_token = ?', (token,)).fetchone()
    conn.close()
    if student:
        return jsonify(dict(student))
    return jsonify({"error": "Aluno não encontrado"}), 404

# ────────────────────────────────────────
# API DE EXERCÍCIOS
# ────────────────────────────────────────
@app.route('/api/exercises', methods=['GET', 'POST'])
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

# ────────────────────────────────────────
# API DE TREINOS
# ────────────────────────────────────────
@app.route('/api/workouts', methods=['POST'])
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
    
    # Limpar progresso antigo do aluno (ficha nova = progresso zerado)
    conn.execute('DELETE FROM workout_progress WHERE student_id = ?', (student_id,))

    # Criar notificação para o ALUNO: "Seu personal atualizou sua ficha!"
    conn.execute('''INSERT INTO notifications (target_role, student_id, student_name, message, type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 ('aluno', student_id, student_name, 
                  f'Seu Personal atualizou sua ficha de treino!', 'workout_updated', now))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Treino enviado com sucesso!"}), 201

@app.route('/api/workouts/<int:student_id>')
def get_workout(student_id):
    conn = get_db_connection()
    workout = conn.execute('SELECT * FROM workouts WHERE student_id = ?', (student_id,)).fetchone()
    conn.close()
    if workout:
        data = json.loads(workout['workout_json'])
        data['updated_at'] = workout['updated_at']
        return jsonify(data)
    return jsonify({"error": "Nenhum treino encontrado"}), 404

# ────────────────────────────────────────
# API DE PROGRESSO DO TREINO
# ────────────────────────────────────────
@app.route('/api/progress/<int:student_id>/<day>', methods=['GET', 'POST'])
def handle_progress(student_id, day):
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    if request.method == 'POST':
        data = request.get_json()
        completed_json = json.dumps(data.get('completedSets', {}))
        conn.execute('''INSERT OR REPLACE INTO workout_progress 
                        (student_id, day, completed_sets_json, updated_at)
                        VALUES (?, ?, ?, ?)''',
                     (student_id, day, completed_json, now))
        conn.commit()
        conn.close()
        return jsonify({"status": "saved"})
    
    progress = conn.execute('SELECT * FROM workout_progress WHERE student_id = ? AND day = ?',
                            (student_id, day)).fetchone()
    conn.close()
    if progress:
        return jsonify(json.loads(progress['completed_sets_json']))
    return jsonify({})

# ────────────────────────────────────────
# API DE FINALIZAÇÃO DE TREINO
# ────────────────────────────────────────
@app.route('/api/workouts/finish', methods=['POST'])
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
    
    # Salvar no histórico
    conn.execute('''INSERT INTO workout_history 
                    (student_id, student_name, day, total_sets, completed_sets, cardio, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (student_id, student_name, day, total_sets, completed_sets, cardio, now))
    
    # Notificar o PROFESSOR
    pct = round((completed_sets / total_sets * 100)) if total_sets > 0 else 0
    msg = f'{student_name} finalizou o treino de {day.upper()} ({pct}% completo)'
    if cardio:
        msg += f' + Cardio: {cardio}'
    
    conn.execute('''INSERT INTO notifications (target_role, student_id, student_name, message, type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 ('professor', student_id, student_name, msg, 'workout_finished', now))
    
    # Atualizar status do aluno
    today = datetime.now().strftime('%d/%m/%Y')
    conn.execute('UPDATE students SET last_workout = ?, status = ? WHERE id = ?', 
                 (today, 'active', student_id))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Treino finalizado! 🔥"})

# ────────────────────────────────────────
# API DE NOTIFICAÇÕES
# ────────────────────────────────────────
@app.route('/api/notifications/<role>')
def get_notifications(role):
    """Busca notificações para 'professor' ou 'aluno'."""
    conn = get_db_connection()
    student_id = request.args.get('student_id')
    
    if role == 'aluno' and student_id:
        notifs = conn.execute(
            'SELECT * FROM notifications WHERE target_role = ? AND student_id = ? ORDER BY created_at DESC LIMIT 20',
            (role, student_id)).fetchall()
    else:
        notifs = conn.execute(
            'SELECT * FROM notifications WHERE target_role = ? ORDER BY created_at DESC LIMIT 20',
            (role,)).fetchall()
    
    conn.close()
    return jsonify([dict(n) for n in notifs])

@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    data = request.get_json()
    role = data.get('role', '')
    student_id = data.get('student_id')
    
    conn = get_db_connection()
    if role == 'aluno' and student_id:
        conn.execute('UPDATE notifications SET is_read = 1 WHERE target_role = ? AND student_id = ?',
                     (role, student_id))
    elif role == 'professor':
        conn.execute('UPDATE notifications SET is_read = 1 WHERE target_role = ?', (role,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/notifications/unread-count/<role>')
def unread_count(role):
    conn = get_db_connection()
    student_id = request.args.get('student_id')
    
    if role == 'aluno' and student_id:
        count = conn.execute(
            'SELECT COUNT(*) FROM notifications WHERE target_role = ? AND student_id = ? AND is_read = 0',
            (role, student_id)).fetchone()[0]
    else:
        count = conn.execute(
            'SELECT COUNT(*) FROM notifications WHERE target_role = ? AND is_read = 0',
            (role,)).fetchone()[0]
    conn.close()
    return jsonify({"count": count})

# ────────────────────────────────────────
# API DE HISTÓRICO
# ────────────────────────────────────────
@app.route('/api/history/<int:student_id>')
def get_history(student_id):
    conn = get_db_connection()
    history = conn.execute(
        'SELECT * FROM workout_history WHERE student_id = ? ORDER BY finished_at DESC LIMIT 30',
        (student_id,)).fetchall()
    conn.close()
    return jsonify([dict(h) for h in history])

@app.route('/api/history/recent')
def recent_history():
    """Últimas atividades de todos os alunos (para dashboard do professor)."""
    conn = get_db_connection()
    history = conn.execute(
        'SELECT * FROM workout_history ORDER BY finished_at DESC LIMIT 20').fetchall()
    conn.close()
    return jsonify([dict(h) for h in history])

# ────────────────────────────────────────
# API DE DESAFIOS GLOBAIS
# ────────────────────────────────────────
@app.route('/api/challenges/active', methods=['GET', 'POST', 'DELETE'])
def handle_active_challenge():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        now = datetime.now().isoformat()
        
        conn.execute('UPDATE challenges SET active = 0')
        
        if data.get('title') and data.get('description'):
            conn.execute('''
                INSERT INTO challenges (title, description, active, created_at)
                VALUES (?, ?, 1, ?)
            ''', (data['title'], data['description'], now))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
        
    elif request.method == 'DELETE':
        conn.execute('UPDATE challenges SET active = 0')
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})
        
    # GET
    challenge = conn.execute('SELECT * FROM challenges WHERE active = 1 ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    if challenge:
        return jsonify(dict(challenge))
    return jsonify({"active": False}), 404

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
