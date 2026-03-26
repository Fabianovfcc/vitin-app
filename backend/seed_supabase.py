"""
Vitin App - Seed Data para Supabase
Popula as tabelas com dados iniciais (exercícios, treinadores, academias, alunos de teste).
Executar UMA VEZ: python -m backend.seed_supabase
"""
import json
import uuid
from datetime import datetime
from backend.supabase_client import supabase

def seed():
    print("Iniciando seed do Supabase...")

    # ── 1. ACADEMIAS ──
    gyms_count = supabase.table('gyms').select('id', count='exact').execute().count or 0
    if gyms_count == 0:
        print("  -> Inserindo academias...")
        supabase.table('gyms').insert([
            {'name': 'Academia Elite Fit', 'owner_name': 'Carlos Magno', 'created_at': datetime.now().isoformat()},
            {'name': 'BlueFit Centro', 'owner_name': 'Roberto Silva', 'created_at': datetime.now().isoformat()}
        ]).execute()

    # ── 2. TREINADORES ──
    trainers_count = supabase.table('trainers').select('id', count='exact').execute().count or 0
    if trainers_count == 0:
        print("  -> Inserindo treinadores elite...")
        elite_trainers = [
            {"name": "Prof. Victor (Vitin)", "specialty": "Bodybuilding & Conditioning", 
             "bio": "Treinador oficial do CT CDE. Especialista em transformações extremas.", 
             "image": "/assets/trainers/vitin.png", "achievement": "Vencedor Arnold Classic South America",
             "password": "vitin123", "status": "active"},
            {"name": "Coach Julio B.", "specialty": "Pro Prep & Performance", 
             "bio": "Conhecido por levar atletas ao limite. Criador do protocolo No Mercy.", 
             "image": "/assets/trainers/julio.png", "achievement": "Trainer de atletas IFBB Pro",
             "password": "123456", "status": "active"},
            {"name": "Edu Corrêa Style", "specialty": "High Intensity Training", 
             "bio": "Foco em falha total e densidade muscular. Treino de pernas legendário.", 
             "image": "/assets/trainers/edu.png", "achievement": "Top 3 Mr. Olympia 212",
             "password": "123456", "status": "active"}
        ]
        result = supabase.table('trainers').insert(elite_trainers).execute()
        
        # Criar catálogo de treinos para cada treinador
        for trainer in result.data:
            tid = trainer['id']
            name = trainer['name']
            sample_protocol = {
                "title": f"Protocolo {name.split()[1]} - Elite",
                "days": ["Sexta - Pernas (Foco Quadríceps)"],
                "exercises": [
                    {"name": "Agachamento Hack", "sets": 4, "reps": "8-12", "load": 120, "obs": "Cadência 4040."},
                    {"name": "Extensora", "sets": 4, "reps": "15+F", "load": 80, "obs": "Drop set 3x."}
                ]
            }
            supabase.table('catalog_workouts').insert({
                'trainer_id': tid,
                'title': f"Leg Day Hardcore ({name.split()[1]})",
                'price': 199.90,
                'description': "Treino de pernas de alta intensidade que desafia seus limites.",
                'workout_json': sample_protocol
            }).execute()

    # ── 3. ALUNOS ──
    students_count = supabase.table('students').select('id', count='exact').execute().count or 0
    if students_count == 0:
        print("  -> Inserindo alunos de teste...")
        supabase.table('students').insert([
            {'name': 'João Silva', 'last_workout': '2026-03-09', 'status': 'active', 'access_token': str(uuid.uuid4())[:8]},
            {'name': 'Maria Oliveira', 'last_workout': '2026-03-10', 'status': 'active', 'access_token': str(uuid.uuid4())[:8]},
            {'name': 'Pedro Santos', 'last_workout': '2026-03-05', 'status': 'late', 'access_token': str(uuid.uuid4())[:8]},
            {'name': 'Fabiano Vieira', 'status': 'active', 'access_token': str(uuid.uuid4())[:8], 'plan_type': 'free'}
        ]).execute()

    # ── 4. EXERCÍCIOS ──
    exercises_count = supabase.table('exercises').select('id', count='exact').execute().count or 0
    if exercises_count == 0:
        print("  -> Inserindo exercícios...")
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
        exercises = []
        for cat, names in all_categories.items():
            for name in names:
                img = "icon:" + cat
                if name == "Supino Reto": img = "/assets/exercises/chest_press.png"
                if name == "Puxada Frente": img = "/assets/exercises/lat_pulldown.png"
                if name == "Elevação Lateral": img = "/assets/exercises/lateral_raise.png"
                if name == "Agachamento Livre": img = "/assets/exercises/squat.png"
                exercises.append({'name': name, 'category': cat, 'image': img})
        
        supabase.table('exercises').insert(exercises).execute()

    # ── 5. VENDAS DE TESTE ──
    sales_count = supabase.table('marketplace_sales').select('id', count='exact').execute().count or 0
    if sales_count == 0:
        print("  -> Inserindo vendas de teste...")
        # Pegar IDs reais
        students = supabase.table('students').select('id').limit(2).execute().data
        workouts = supabase.table('catalog_workouts').select('id, trainer_id').limit(1).execute().data
        if students and workouts:
            w = workouts[0]
            for s in students:
                supabase.table('marketplace_sales').insert({
                    'workout_id': w['id'], 'trainer_id': w['trainer_id'],
                    'student_id': s['id'], 'price': 199.90,
                    'created_at': datetime.now().isoformat()
                }).execute()

    print("Seed completo!")


if __name__ == '__main__':
    seed()
