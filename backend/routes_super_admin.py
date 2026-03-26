from flask import Blueprint, jsonify, request
import os
from .supabase_client import supabase

super_admin_bp = Blueprint('super_admin', __name__)

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
    total_trainers = supabase.table('trainers').select('id', count='exact').execute().count or 0
    total_students = supabase.table('students').select('id', count='exact').execute().count or 0
    total_gyms = supabase.table('gyms').select('id', count='exact').execute().count or 0
    active_subs = supabase.table('students').select('id', count='exact').eq('plan_type', 'premium').execute().count or 0
    recent = supabase.table('workout_history').select('id', count='exact').execute().count or 0

    churn_count = 0  # Supabase date filtering will be added in V2
    stats = {
        "total_trainers": total_trainers,
        "total_students": total_students,
        "total_gyms": total_gyms,
        "active_subscriptions": active_subs,
        "recent_activity": recent,
        "churn_rate": 0
    }
    return jsonify(stats)

@super_admin_bp.route('/gyms', methods=['GET', 'POST'])
@require_super_auth
def manage_gyms():
    if request.method == 'POST':
        data = request.get_json()
        from datetime import datetime
        result = supabase.table('gyms').insert({
            'name': data['name'], 'owner_name': data['owner_name'],
            'plan': data.get('plan', 'premium'), 'created_at': datetime.now().isoformat()
        }).execute()
        new_id = result.data[0]['id'] if result.data else None
        return jsonify({"status": "success", "id": new_id})
    
    result = supabase.table('gyms').select('*').execute()
    return jsonify(result.data)

@super_admin_bp.route('/gyms/<int:gym_id>', methods=['PUT', 'DELETE'])
@require_super_auth
def manage_gym_detail(gym_id):
    if request.method == 'DELETE':
        supabase.table('trainers').update({'gym_id': None}).eq('gym_id', gym_id).execute()
        supabase.table('gyms').delete().eq('id', gym_id).execute()
        return jsonify({"status": "success"})
    
    data = request.json
    supabase.table('gyms').update({
        'name': data['name'], 'owner_name': data['owner_name'], 'plan': data.get('plan')
    }).eq('id', gym_id).execute()
    return jsonify({"status": "success"})

@super_admin_bp.route('/trainers-detailed')
@require_super_auth
def trainers_detailed():
    result = supabase.table('trainers').select('*, gyms(name)').execute()
    trainers = []
    for t in result.data:
        t_dict = dict(t)
        # Conta alunos deste treinador
        count_result = supabase.table('students').select('id', count='exact').eq('trainer_id', t['id']).execute()
        t_dict['student_count'] = count_result.count or 0
        t_dict['gym_name'] = t.get('gyms', {}).get('name') if t.get('gyms') else None
        if 'gyms' in t_dict:
            del t_dict['gyms']
        trainers.append(t_dict)
    return jsonify(trainers)

@super_admin_bp.route('/trainers/<int:trainer_id>', methods=['DELETE'])
@require_super_auth
def delete_trainer(trainer_id):
    supabase.table('students').update({'trainer_id': None}).eq('trainer_id', trainer_id).execute()
    supabase.table('trainers').delete().eq('id', trainer_id).execute()
    return jsonify({"status": "success", "message": "Professor excluído."})

@super_admin_bp.route('/trainer-students/<int:trainer_id>')
@require_super_auth
def get_trainer_students(trainer_id):
    result = supabase.table('students').select('id, name, whatsapp, status').eq('trainer_id', trainer_id).execute()
    return jsonify(result.data)

@super_admin_bp.route('/trainers', methods=['POST'])
@require_super_auth
def create_trainer():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Nome obrigatório"}), 400
    
    try:
        result = supabase.table('trainers').insert({
            'name': name, 'password': data.get('password', '123456'),
            'gym_id': data.get('gym_id'), 'whatsapp': data.get('whatsapp'), 'status': 'active'
        }).execute()
        new_id = result.data[0]['id'] if result.data else None
        return jsonify({"status": "success", "id": new_id})
    except Exception as e:
        print(f"ERRO AO CRIAR PROFESSOR: {e}")
        return jsonify({"error": str(e)}), 500

@super_admin_bp.route('/trainers/<int:trainer_id>', methods=['PUT'])
@require_super_auth
def update_trainer(trainer_id):
    data = request.json
    supabase.table('trainers').update({
        'name': data.get('name'), 'gym_id': data.get('gym_id'), 'whatsapp': data.get('whatsapp')
    }).eq('id', trainer_id).execute()
    return jsonify({"status": "success"})

@super_admin_bp.route('/students-all')
@require_super_auth
def get_all_students_global():
    result = supabase.table('students').select('*, trainers(name)').execute()
    students = []
    for s in result.data:
        s_dict = dict(s)
        s_dict['trainer_name'] = s.get('trainers', {}).get('name') if s.get('trainers') else None
        if 'trainers' in s_dict:
            del s_dict['trainers']
        students.append(s_dict)
    return jsonify(students)

@super_admin_bp.route('/students/<int:student_id>', methods=['DELETE'])
@require_super_auth
def delete_student_global(student_id):
    supabase.table('students').delete().eq('id', student_id).execute()
    return jsonify({"status": "success"})

@super_admin_bp.route('/students', methods=['POST', 'PUT'])
@require_super_auth
def manage_students_global():
    data = request.json
    try:
        if request.method == 'POST':
            from datetime import datetime
            result = supabase.table('students').insert({
                'name': data['name'], 'whatsapp': data.get('whatsapp'),
                'trainer_id': data.get('trainer_id'), 'age': data.get('age'),
                'weight': data.get('weight'), 'goal': data.get('goal'),
                'status': 'Ativo', 'created_at': datetime.now().isoformat(), 'plan_type': 'free'
            }).execute()
            new_id = result.data[0]['id'] if result.data else None
            return jsonify({"status": "success", "id": new_id})
        else:
            supabase.table('students').update({
                'name': data['name'], 'whatsapp': data.get('whatsapp'),
                'trainer_id': data.get('trainer_id'), 'age': data.get('age'),
                'weight': data.get('weight'), 'goal': data.get('goal'),
                'status': data.get('status')
            }).eq('id', data['id']).execute()
            return jsonify({"status": "success"})
    except Exception as e:
        print(f"ERRO AO GERIR ALUNO GLOBAL: {e}")
        return jsonify({"error": str(e)}), 500

@super_admin_bp.route('/billing-data')
@require_super_auth
def get_billing_data():
    total_students = supabase.table('students').select('id', count='exact').execute().count or 0
    active_gyms = supabase.table('gyms').select('id', count='exact').execute().count or 0
    
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
    total_rev_result = supabase.table('marketplace_sales').select('price').execute()
    total_revenue = sum(float(s['price']) for s in total_rev_result.data) if total_rev_result.data else 0
    total_sales = len(total_rev_result.data)
    
    # Top trainer
    top_trainer = "Sem Vendas"
    if total_rev_result.data:
        from collections import Counter
        trainer_counts = Counter(s.get('trainer_id') for s in total_rev_result.data)
        top_id = trainer_counts.most_common(1)[0][0]
        top_result = supabase.table('trainers').select('name').eq('id', top_id).execute()
        if top_result.data:
            top_trainer = top_result.data[0]['name']
    
    stats = {
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "top_trainer": top_trainer
    }
    
    # Ranking
    trainers_result = supabase.table('trainers').select('id, name').execute()
    ranking = []
    for t in trainers_result.data:
        t_sales = supabase.table('marketplace_sales').select('price').eq('trainer_id', t['id']).execute()
        if t_sales.data:
            ranking.append({
                'name': t['name'],
                'sales_count': len(t_sales.data),
                'revenue': sum(float(s['price']) for s in t_sales.data)
            })
    ranking.sort(key=lambda x: x['sales_count'], reverse=True)
    
    # Recent sales
    recent_result = supabase.table('marketplace_sales').select(
        '*, students(name), catalog_workouts(title)'
    ).order('created_at', desc=True).limit(10).execute()
    
    recent_sales = []
    for s in recent_result.data:
        recent_sales.append({
            'created_at': s['created_at'],
            'student_name': s.get('students', {}).get('name', '') if s.get('students') else '',
            'workout_title': s.get('catalog_workouts', {}).get('title', '') if s.get('catalog_workouts') else '',
            'price': s['price']
        })
    
    return jsonify({
        "stats": stats,
        "ranking": ranking,
        "recent_sales": recent_sales
    })

@super_admin_bp.route('/feed', methods=['GET'])
@require_super_auth
def mod_get_feed():
    result = supabase.table('feed_posts').select('*').order('created_at', desc=True).execute()
    return jsonify(result.data)

@super_admin_bp.route('/feed/<int:post_id>', methods=['DELETE'])
@require_super_auth
def mod_delete_post(post_id):
    supabase.table('feed_posts').delete().eq('id', post_id).execute()
    return jsonify({"status": "success", "message": "Post removido."})

@super_admin_bp.route('/catalog-mgmt', methods=['GET', 'POST', 'PUT'])
@require_super_auth
def manage_catalog():
    if request.method == 'GET':
        result = supabase.table('catalog_workouts').select('*, trainers(name)').execute()
        workouts = []
        for w in result.data:
            w_dict = dict(w)
            w_dict['trainer_name'] = w.get('trainers', {}).get('name', '') if w.get('trainers') else ''
            if 'trainers' in w_dict:
                del w_dict['trainers']
            workouts.append(w_dict)
        return jsonify(workouts)
    
    data = request.json
    if request.method == 'POST':
        supabase.table('catalog_workouts').insert({
            'trainer_id': data['trainer_id'], 'title': data['title'],
            'description': data['description'], 'price': float(data['price']),
            'image': data.get('image', ''), 'workout_json': {}
        }).execute()
    elif request.method == 'PUT':
        supabase.table('catalog_workouts').update({
            'title': data['title'], 'description': data['description'],
            'price': float(data['price']), 'image': data.get('image')
        }).eq('id', data['id']).execute()
    
    return jsonify({"status": "success"})

@super_admin_bp.route('/catalog-mgmt/<int:workout_id>', methods=['DELETE'])
@require_super_auth
def delete_catalog_workout(workout_id):
    supabase.table('catalog_workouts').delete().eq('id', workout_id).execute()
    return jsonify({"status": "success"})

@super_admin_bp.route('/exercises', methods=['GET', 'POST'])
@require_super_auth
def manage_exercises():
    if request.method == 'POST':
        data = request.json
        if data.get('id'):
            supabase.table('exercises').update({
                'name': data['name'], 'category': data['category'], 'image': data['image']
            }).eq('id', data['id']).execute()
        else:
            supabase.table('exercises').insert({
                'name': data['name'], 'category': data['category'], 'image': data['image']
            }).execute()
        return jsonify({"status": "success"})
    
    result = supabase.table('exercises').select('*').order('category').order('name').execute()
    return jsonify(result.data)

@super_admin_bp.route('/exercises/<int:ex_id>', methods=['DELETE'])
@require_super_auth
def delete_exercise(ex_id):
    supabase.table('exercises').delete().eq('id', ex_id).execute()
    return jsonify({"status": "success"})
