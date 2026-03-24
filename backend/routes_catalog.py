from flask import Blueprint, jsonify, request
from .database import get_db_connection

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/api/catalog')
def get_catalog():
    conn = get_db_connection()
    trainers = conn.execute('SELECT * FROM trainers').fetchall()
    catalog = []
    
    for t in trainers:
        trainer_dict = dict(t)
        workouts = conn.execute('SELECT * FROM catalog_workouts WHERE trainer_id = ?', (t['id'],)).fetchall()
        trainer_dict['workouts'] = [dict(w) for w in workouts]
        catalog.append(trainer_dict)
        
    conn.close()
    return jsonify(catalog)

@catalog_bp.route('/api/catalog/buy', methods=['POST'])
def buy_workout():
    data = request.get_json()
    student_id = data.get('student_id')
    workout_id = data.get('workout_id')
    
    conn = get_db_connection()
    # Pegar info do workout
    workout = conn.execute('SELECT * FROM catalog_workouts WHERE id = ?', (workout_id,)).fetchone()
    if not workout:
        conn.close()
        return jsonify({"error": "Protocolo não encontrado"}), 404
        
    from datetime import datetime
    conn.execute('''
        INSERT INTO marketplace_sales (workout_id, trainer_id, student_id, price, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (workout_id, workout['trainer_id'], student_id, workout['price'], datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Protocolo adquirido com sucesso! 🔥 Redirecionando..."})
