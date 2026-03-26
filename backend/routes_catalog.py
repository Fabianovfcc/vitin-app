from flask import Blueprint, jsonify, request
from .supabase_client import supabase

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/api/catalog')
def get_catalog():
    trainers_result = supabase.table('trainers').select('*').execute()
    catalog = []
    
    for t in trainers_result.data:
        trainer_dict = dict(t)
        workouts_result = supabase.table('catalog_workouts').select('*').eq('trainer_id', t['id']).execute()
        trainer_dict['workouts'] = workouts_result.data
        catalog.append(trainer_dict)
        
    return jsonify(catalog)

@catalog_bp.route('/api/catalog/buy', methods=['POST'])
def buy_workout():
    data = request.get_json()
    student_id = data.get('student_id')
    workout_id = data.get('workout_id')
    
    result = supabase.table('catalog_workouts').select('*').eq('id', workout_id).execute()
    if not result.data:
        return jsonify({"error": "Protocolo não encontrado"}), 404
    
    workout = result.data[0]
    from datetime import datetime
    supabase.table('marketplace_sales').insert({
        'workout_id': workout_id,
        'trainer_id': workout['trainer_id'],
        'student_id': student_id,
        'price': float(workout['price']),
        'created_at': datetime.now().isoformat()
    }).execute()
    
    return jsonify({"status": "success", "message": "Protocolo adquirido com sucesso! 🔥 Redirecionando..."})
