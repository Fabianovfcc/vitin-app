import sqlite3
import os
import json
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'vitin.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
            whatsapp TEXT,
            trainer_id INTEGER,
            gym_id INTEGER,
            age TEXT,
            weight TEXT,
            goal TEXT,
            status TEXT DEFAULT 'active',
            plan_type TEXT DEFAULT 'free',
            subscription_expires_at TEXT,
            access_token TEXT UNIQUE,
            created_at TEXT,
            last_workout TEXT
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
    
    # Tabela de Feed de Resultados (Social Proof) - Expira em 24h
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feed_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            student_name TEXT,
            image_url TEXT NOT NULL,
            caption TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    # Tabela de Treinadores Elite (Marketplace)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trainers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            password TEXT,
            gym_id INTEGER,
            whatsapp TEXT,
            status TEXT DEFAULT 'active',
            specialty TEXT,
            bio TEXT,
            image TEXT,
            achievement TEXT
        )
    ''')
    
    # Tabela de Academias (Novo!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_name TEXT,
            plan TEXT DEFAULT 'premium',
            created_at TEXT NOT NULL
        )
    ''')

    # Tabela de Catálogo de Treinos (Marketplace)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            workout_json TEXT NOT NULL,
            FOREIGN KEY (trainer_id) REFERENCES trainers(id)
        )
    ''')
    
    # Tabela de Vendas do Marketplace (Novo!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marketplace_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            price REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (workout_id) REFERENCES catalog_workouts(id),
            FOREIGN KEY (trainer_id) REFERENCES trainers(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    # Migrações Individuais (Garantir que todas as colunas existam uma por uma)
    def add_col_if_missing(table, col, definition):
        try:
            cursor.execute(f"SELECT {col} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            print(f"Migrando: Adicionando {col} em {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

    # Estudantes
    add_col_if_missing("students", "whatsapp", "TEXT")
    add_col_if_missing("students", "trainer_id", "INTEGER")
    add_col_if_missing("students", "gym_id", "INTEGER")
    add_col_if_missing("students", "age", "TEXT")
    add_col_if_missing("students", "weight", "TEXT")
    add_col_if_missing("students", "goal", "TEXT")
    add_col_if_missing("students", "plan_type", "TEXT DEFAULT 'free'")
    add_col_if_missing("students", "subscription_expires_at", "TEXT")
    add_col_if_missing("students", "access_token", "TEXT UNIQUE")
    add_col_if_missing("students", "created_at", "TEXT")

    # Professores
    add_col_if_missing("trainers", "password", "TEXT")
    add_col_if_missing("trainers", "gym_id", "INTEGER")
    add_col_if_missing("trainers", "whatsapp", "TEXT")
    add_col_if_missing("trainers", "status", "TEXT DEFAULT 'active'")

    # Seed data
    cursor.execute('SELECT COUNT(*) FROM students')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('João Silva', '2026-03-09', 'active', str(uuid.uuid4())[:8]))
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('Maria Oliveira', '2026-03-10', 'active', str(uuid.uuid4())[:8]))
        cursor.execute("INSERT INTO students (name, last_workout, status, access_token) VALUES (?, ?, ?, ?)",
                       ('Pedro Santos', '2026-03-05', 'late', str(uuid.uuid4())[:8]))
    else:
        students_without_token = cursor.execute("SELECT id FROM students WHERE access_token IS NULL").fetchall()
        for s in students_without_token:
            cursor.execute("UPDATE students SET access_token = ? WHERE id = ?", (str(uuid.uuid4())[:8], s['id']))

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

    cursor.execute('SELECT COUNT(*) FROM trainers')
    if cursor.fetchone()[0] == 0:
        elite_trainers = [
            ("Prof. Victor (Vitin)", "Bodybuilding & Conditioning", "Treinador oficial do CT CDE. Especialista em transformações extremas.", "/assets/trainers/vitin.png", "Vencedor Arnold Classic South America"),
            ("Coach Julio B.", "Pro Prep & Performance", "Conhecido por levar atletas ao limite. Criador do protocolo No Mercy.", "/assets/trainers/julio.png", "Trainer de atletas IFBB Pro"),
            ("Edu Corrêa Style", "High Intensity Training", "Foco em falha total e densidade muscular. Treino de pernas legendário.", "/assets/trainers/edu.png", "Top 3 Mr. Olympia 212")
        ]
        for name, spec, bio, img, ach in elite_trainers:
            cursor.execute("INSERT INTO trainers (name, specialty, bio, image, achievement) VALUES (?, ?, ?, ?, ?)", (name, spec, bio, img, ach))
            tid = cursor.lastrowid
            sample_protocol = json.dumps({
                "title": f"Protocolo {name.split()[1]} - Elite",
                "days": ["Sexta - Pernas (Foco Quadríceps)"],
                "exercises": [
                    {"name": "Agachamento Hack", "sets": 4, "reps": "8-12", "load": 120, "obs": "Cadência 4040. Falha total na última série."},
                    {"name": "Extensora", "sets": 4, "reps": "15+F", "load": 80, "obs": "Drop set 3x na última série."}
                ]
            })
            cursor.execute("INSERT INTO catalog_workouts (trainer_id, title, price, description, workout_json) VALUES (?, ?, ?, ?, ?)", 
                           (tid, f"Leg Day Hardcore ({name.split()[1]})", 199.90, "Treino de pernas de alta intensidade que desafia seus limites.", sample_protocol))

    cursor.execute('SELECT COUNT(*) FROM gyms')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO gyms (name, owner_name, created_at) VALUES (?, ?, ?)",
                       ('Academia Elite Fit', 'Carlos Magno', datetime.now().isoformat()))
        cursor.execute("INSERT INTO gyms (name, owner_name, created_at) VALUES (?, ?, ?)",
                       ('BlueFit Centro', 'Roberto Silva', datetime.now().isoformat()))

    # Seed de Vendas (Marketplace)
    cursor.execute('SELECT COUNT(*) FROM marketplace_sales')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO marketplace_sales (workout_id, trainer_id, student_id, price, created_at) VALUES (?, ?, ?, ?, ?)",
                       (1, 1, 1, 199.90, datetime.now().isoformat()))
        cursor.execute("INSERT INTO marketplace_sales (workout_id, trainer_id, student_id, price, created_at) VALUES (?, ?, ?, ?, ?)",
                       (1, 1, 2, 199.90, datetime.now().isoformat()))

    conn.commit()
    conn.close()
