from flask import Blueprint, jsonify, request
import json
import uuid
from datetime import datetime
from .supabase_client import supabase

students_bp = Blueprint('students', __name__)

@students_bp.route('/api/students', methods=['GET', 'POST'])
def handle_students():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        whatsapp = data.get('whatsapp')
        token = str(uuid.uuid4())[:8]
        result = supabase.table('students').insert({
            'name': name, 'whatsapp': whatsapp, 'access_token': token
        }).execute()
        new_student = result.data[0] if result.data else {}
        return jsonify({"status": "success", "id": new_student.get('id'), "access_token": token, "whatsapp": whatsapp}), 201
    
    result = supabase.table('students').select('*').execute()
    return jsonify(result.data)

@students_bp.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    supabase.table('workout_progress').delete().eq('student_id', id).execute()
    supabase.table('notifications').delete().eq('student_id', id).execute()
    supabase.table('workouts').delete().eq('student_id', id).execute()
    supabase.table('students').delete().eq('id', id).execute()
    return jsonify({"status": "success"})

@students_bp.route('/api/students/by-token/<token>')
def get_student_by_token(token):
    result = supabase.table('students').select('*').eq('access_token', token).execute()
    if result.data:
        return jsonify(result.data[0])
    return jsonify({"error": "Aluno não encontrado"}), 404

@students_bp.route('/api/students/by-whatsapp/<whatsapp>')
def get_student_by_whatsapp(whatsapp):
    result = supabase.table('students').select('*').eq('whatsapp', whatsapp).execute()
    if result.data:
        return jsonify(result.data[0])
    return jsonify({"error": "Aluno não encontrado"}), 404

@students_bp.route('/api/student/purchases', methods=['GET'])
def get_student_purchases():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id obrigatório"}), 400
    
    result = supabase.table('marketplace_sales').select(
        '*, catalog_workouts(id, title), trainers(name)'
    ).eq('student_id', student_id).execute()
    
    purchases = []
    for sale in result.data:
        purchases.append({
            'id': sale['catalog_workouts']['id'] if sale.get('catalog_workouts') else None,
            'title': sale['catalog_workouts']['title'] if sale.get('catalog_workouts') else '',
            'trainer_name': sale['trainers']['name'] if sale.get('trainers') else '',
            'price': sale['price'],
            'created_at': sale['created_at']
        })
    return jsonify(purchases)

@students_bp.route('/api/analytics/track', methods=['POST'])
def track_analytics():
    data = request.json
    print(f"ANALYTICS: Evento '{data.get('event_type')}' do aluno {data.get('student_id')}")
    return jsonify({"status": "captured"})

@students_bp.route('/api/students/profile', methods=['PUT', 'POST'])
def update_student_profile():
    data = request.json
    student_id = data.get('id')
    supabase.table('students').update({
        'weight': data.get('weight'),
        'height': data.get('height'),
        'goal': data.get('goal'),
        'anamnesis_done': True
    }).eq('id', student_id).execute()
    return jsonify({"status": "updated"})
