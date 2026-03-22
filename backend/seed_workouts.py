import sqlite3
import json
from datetime import datetime
import os

db_path = r"c:\Users\accou\Desktop\Antigravity\App Vitin - Fichas de treino\backend\data\vitin.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Dados de exemplo de treino
sample_workout = {
    "student_id": 4,
    "student_name": "Fabiano Vieira",
    "date": datetime.now().strftime("%d/%m/%Y"),
    "weeklyWorkouts": {
        "seg": [{"name": "Supino Reto", "sets": "4", "reps": "12", "load": "60", "image": "/assets/exercises/chest_press.png", "category": "Peito", "obs": "Controlar a descida"}],
        "ter": [{"name": "Puxada Frente", "sets": "4", "reps": "12", "load": "50", "image": "/assets/exercises/lat_pulldown.png", "category": "Costas"}],
        "qua": [{"name": "Agachamento Livre", "sets": "4", "reps": "10", "load": "80", "image": "/assets/exercises/squat.png", "category": "Pernas"}],
        "qui": [{"name": "Elevação Lateral", "sets": "4", "reps": "15", "load": "10", "image": "/assets/exercises/lateral_raise.png", "category": "Ombros"}],
        "sex": [
            {"name": "Rosca Direta", "sets": "3", "reps": "12", "load": "15", "image": "icon:Bíceps", "category": "Bíceps"},
            {"name": "Tríceps Pulley", "sets": "3", "reps": "12", "load": "20", "image": "icon:Tríceps", "category": "Tríceps"}
        ],
        "sab": [],
        "dom": []
    },
    "weeklyCardio": {
        "seg": {"type": "Esteira", "time": "20"},
        "ter": {"type": "Bicicleta", "time": "15"},
        "qua": {"type": "", "time": ""},
        "qui": {"type": "Caminhada", "time": "30"},
        "sex": {"type": "Elíptico", "time": "15"},
        "sab": {"type": "", "time": ""},
        "dom": {"type": "", "time": ""}
    }
}

now_iso = datetime.now().isoformat()

# Adicionar para todos os alunos (IDs 1 a 5)
for i in range(1, 6):
    workout_json = json.dumps(sample_workout)
    cursor.execute('INSERT OR REPLACE INTO workouts (student_id, workout_json, date, updated_at) VALUES (?, ?, ?, ?)',
                   (i, workout_json, sample_workout["date"], now_iso))

conn.commit()
conn.close()
print("Treinos de exemplo adicionados para todos os alunos.")
