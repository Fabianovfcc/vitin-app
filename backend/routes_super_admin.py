from flask import Blueprint, jsonify, request
import os
from .database import get_db_connection
from .auth import require_auth

super_admin_bp = Blueprint('super_admin', __name__)

# O dono do app usa a mesma senha de admin ou uma MASTER_PASSWORD
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "master_vitin_2024")

def require_super_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # TEMPORARIAMENTE PERMISSIVO PARA DEBUG
        return f(*args, **kwargs)
    return decorated

@super_admin_bp.route('/stats')
@require_super_auth
def global_stats():
    conn = get_db_connection()
    
    # Estatísticas Avançadas
    stats = {
        "total_trainers": conn.execute('SELECT COUNT(*) FROM trainers').fetchone()[0],
        "total_students": conn.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        "total_gyms": conn.execute('SELECT COUNT(*) FROM gyms').fetchone()[0],
        "active_subscriptions": conn.execute("SELECT COUNT(*) FROM students WHERE plan_type = 'premium'").fetchone()[0],
        "recent_activity": conn.execute("SELECT COUNT(*) FROM workout_history WHERE finished_at > date('now', '-7 days')").fetchone()[0]
    }
    
    # Churn Rate Estimado (alunos sem treino há 10 dias)
    churn_count = conn.execute("SELECT COUNT(*) FROM students WHERE last_workout < date('now', '-10 days')").fetchone()[0]
    stats["churn_rate"] = round((churn_count / stats["total_students"] * 100), 1) if stats["total_students"] > 0 else 0
    
    conn.close()
    return jsonify(stats)

@super_admin_bp.route('/gyms', methods=['GET', 'POST'])
@require_super_auth
def manage_gyms():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        from datetime import datetime
        cursor = conn.execute('INSERT INTO gyms (name, owner_name, plan, created_at) VALUES (?, ?, ?, ?)',
                     (data['name'], data['owner_name'], data.get('plan', 'premium'), datetime.now().isoformat()))
        new_id = cursor.lastrowid
        conn.commit()
        return jsonify({"status": "success", "id": new_id})
    
    gyms = conn.execute('SELECT * FROM gyms').fetchall()
    conn.close()
    return jsonify([dict(g) for g in gyms])

@super_admin_bp.route('/gyms/<int:gym_id>', methods=['PUT', 'DELETE'])
@require_super_auth
def manage_gym_detail(gym_id):
    conn = get_db_connection()
    if request.method == 'DELETE':
        # Antes de excluir, desassociar professores
        conn.execute('UPDATE trainers SET gym_id = NULL WHERE gym_id = ?', (gym_id,))
        conn.execute('DELETE FROM gyms WHERE id = ?', (gym_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    data = request.json
    conn.execute('UPDATE gyms SET name = ?, owner_name = ?, plan = ? WHERE id = ?',
                 (data['name'], data['owner_name'], data.get('plan'), gym_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@super_admin_bp.route('/trainers-detailed')
@require_super_auth
def trainers_detailed():
    conn = get_db_connection()
    # Pega professores e conta quantos alunos cada um tem
    query = '''
        SELECT t.*, 
               (SELECT COUNT(*) FROM students s WHERE s.trainer_id = t.id) as student_count,
               g.name as gym_name
        FROM trainers t
        LEFT JOIN gyms g ON t.gym_id = g.id
    '''
    trainers = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(t) for t in trainers])

@super_admin_bp.route('/trainers/<int:trainer_id>', methods=['DELETE'])
@require_super_auth
def delete_trainer(trainer_id):
    conn = get_db_connection()
    conn.execute('UPDATE students SET trainer_id = NULL WHERE trainer_id = ?', (trainer_id,))
    conn.execute('DELETE FROM trainers WHERE id = ?', (trainer_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Professor excluído."})

@super_admin_bp.route('/trainer-students/<int:trainer_id>')
@require_super_auth
def get_trainer_students(trainer_id):
    conn = get_db_connection()
    students = conn.execute('SELECT id, name, whatsapp, status FROM students WHERE trainer_id = ?', (trainer_id,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@super_admin_bp.route('/trainers', methods=['POST'])
@require_super_auth
def create_trainer():
    data = request.json
    name = data.get('name')
    gym_id = data.get('gym_id')
    password = data.get('password', '123456') # Senha padrão
    
    if not name: return jsonify({"error": "Nome obrigatório"}), 400
    
    conn = get_db_connection()
    try:
        cur = conn.execute('INSERT INTO trainers (name, password, gym_id, whatsapp, status) VALUES (?, ?, ?, ?, ?)', 
                           (name, password, gym_id, data.get('whatsapp'), 'active'))
        new_id = cur.lastrowid
        conn.commit()
        return jsonify({"status": "success", "id": new_id})
    except Exception as e:
        print(f"ERRO AO CRIAR PROFESSOR: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@super_admin_bp.route('/trainers/<int:trainer_id>', methods=['PUT'])
@require_super_auth
def update_trainer(trainer_id):
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE trainers SET name = ?, gym_id = ?, whatsapp = ? WHERE id = ?', 
                 (data.get('name'), data.get('gym_id'), data.get('whatsapp'), trainer_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@super_admin_bp.route('/students-all')
@require_super_auth
def get_all_students_global():
    conn = get_db_connection()
    students = conn.execute('''
        SELECT s.*, t.name as trainer_name 
        FROM students s
        LEFT JOIN trainers t ON s.trainer_id = t.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@super_admin_bp.route('/students/<int:student_id>', methods=['DELETE'])
@require_super_auth
def delete_student_global(student_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@super_admin_bp.route('/students', methods=['POST', 'PUT'])
@require_super_auth
def manage_students_global():
    conn = get_db_connection()
    data = request.json
    try:
        if request.method == 'POST':
            from datetime import datetime
            cursor = conn.execute('''
                INSERT INTO students (name, whatsapp, trainer_id, age, weight, goal, status, created_at, plan_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['whatsapp'], data.get('trainer_id'), data.get('age'), 
                  data.get('weight'), data.get('goal'), 'Ativo', datetime.now().isoformat(), 'free'))
            new_id = cursor.lastrowid
            conn.commit()
            return jsonify({"status": "success", "id": new_id})
        else:
            cur = conn.execute('''
                UPDATE students SET name=?, whatsapp=?, trainer_id=?, age=?, weight=?, goal=?, status=?
                WHERE id=?
            ''', (data['name'], data['whatsapp'], data.get('trainer_id'), data.get('age'), 
                  data.get('weight'), data.get('goal'), data.get('status'), data['id']))
            conn.commit()
            print(f"ALUNO ATUALIZADO: ID {data['id']}, Linhas afetadas: {cur.rowcount}")
            return jsonify({"status": "success", "affected": cur.rowcount})
    except Exception as e:
        print(f"ERRO AO GERIR ALUNO GLOBAL: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@super_admin_bp.route('/billing-data')
@require_super_auth
def get_billing_data():
    # Simulação de dados financeiros reais baseados na DB
    conn = get_db_connection()
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    active_gyms = conn.execute('SELECT COUNT(*) FROM gyms').fetchone()[0]
    conn.close()
    
    return jsonify({
        "mrr": total_students * 29.90,
        "gym_revenue": active_gyms * 199.00,
        "transactions": [
            {"id": 1, "client": "Academia Alpha", "value": 199.00, "date": "2024-03-20"},
            {"id": 2, "client": "Aluno João", "value": 29.90, "date": "2024-03-21"},
        ]
    })

@super_admin_bp.route('/marketplace-data')
@require_super_auth
def get_marketplace_data():
    conn = get_db_connection()
    
    # KPIs do Marketplace
    stats = {
        "total_revenue": conn.execute('SELECT SUM(price) FROM marketplace_sales').fetchone()[0] or 0,
        "total_sales": conn.execute('SELECT COUNT(*) FROM marketplace_sales').fetchone()[0],
        "top_trainer": conn.execute('''
            SELECT name FROM trainers 
            WHERE id = (SELECT trainer_id FROM marketplace_sales GROUP BY trainer_id ORDER BY COUNT(*) DESC LIMIT 1)
        ''').fetchone()
    }
    stats["top_trainer"] = stats["top_trainer"][0] if stats["top_trainer"] else "Sem Vendas"
    
    # Ranking de Vendas por Professor
    ranking = conn.execute('''
        SELECT t.name, COUNT(s.id) as sales_count, SUM(s.price) as revenue
        FROM trainers t
        JOIN marketplace_sales s ON t.id = s.trainer_id
        GROUP BY t.id
        ORDER BY sales_count DESC
    ''').fetchall()
    
    # Vendas Recentes
    recent_sales = conn.execute('''
        SELECT s.created_at, st.name as student_name, w.title as workout_title, s.price
        FROM marketplace_sales s
        JOIN students st ON s.student_id = st.id
        JOIN catalog_workouts w ON s.workout_id = w.id
        ORDER BY s.created_at DESC LIMIT 10
    ''').fetchall()
    
    conn.close()
    return jsonify({
        "stats": stats,
        "ranking": [dict(r) for r in ranking],
        "recent_sales": [dict(s) for s in recent_sales]
    })

@super_admin_bp.route('/feed', methods=['GET'])
@require_super_auth
def mod_get_feed():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM feed_posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(p) for p in posts])

@super_admin_bp.route('/feed/<int:post_id>', methods=['DELETE'])
@require_super_auth
def mod_delete_post(post_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM feed_posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Post removido."})

@super_admin_bp.route('/catalog-mgmt', methods=['GET', 'POST', 'PUT'])
@require_super_auth
def manage_catalog():
    conn = get_db_connection()
    if request.method == 'GET':
        workouts = conn.execute('''
            SELECT w.*, t.name as trainer_name 
            FROM catalog_workouts w
            JOIN trainers t ON w.trainer_id = t.id
        ''').fetchall()
        conn.close()
        return jsonify([dict(w) for w in workouts])
    
    data = request.json
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO catalog_workouts (trainer_id, title, description, price, image)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['trainer_id'], data['title'], data['description'], data['price'], data.get('image', '')))
        conn.commit()
    elif request.method == 'PUT':
        conn.execute('''
            UPDATE catalog_workouts SET title = ?, description = ?, price = ?, image = ?
            WHERE id = ?
        ''', (data['title'], data['description'], data['price'], data.get('image'), data['id']))
        conn.commit()
    
    conn.close()
    return jsonify({"status": "success"})

@super_admin_bp.route('/catalog-mgmt/<int:workout_id>', methods=['DELETE'])
@require_super_auth
def delete_catalog_workout(workout_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM catalog_workouts WHERE id = ?', (workout_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# --- GESTÃO GLOBAL DE EXERCÍCIOS ---
@super_admin_bp.route('/exercises', methods=['GET', 'POST'])
@require_super_auth
def manage_exercises():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        if data.get('id'):
            cur = conn.execute('UPDATE exercises SET name = ?, category = ?, image = ? WHERE id = ?',
                         (data['name'], data['category'], data['image'], data['id']))
            print(f"EXERCICIO ATUALIZADO: ID {data['id']}, Linhas afetadas: {cur.rowcount}")
        else:
            cur = conn.execute('INSERT INTO exercises (name, category, image) VALUES (?, ?, ?)',
                         (data['name'], data['category'], data['image']))
            print(f"EXERCICIO CRIADO: ID {cur.lastrowid}")
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    
    exercises = conn.execute('SELECT * FROM exercises ORDER BY category, name').fetchall()
    conn.close()
    return jsonify([dict(e) for e in exercises])

@super_admin_bp.route('/exercises/<int:ex_id>', methods=['DELETE'])
@require_super_auth
def delete_exercise(ex_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM exercises WHERE id = ?', (ex_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})
