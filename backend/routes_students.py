from flask import Blueprint, jsonify, request
import json
import uuid
from datetime import datetime
from .supabase_client import supabase
from .auth_logic import hash_pin, verify_pin, format_phone
import jwt
import os

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


@students_bp.route('/api/auth/check-user', methods=['POST'])
def check_user():
    data = request.json
    phone = format_phone(data.get('phone'))
    
    if not phone:
        return jsonify({"error": "Telefone é obrigatório"}), 400

    result = supabase.table('students').select('*').or_(f"phone_auth.eq.{phone},whatsapp.eq.{data.get('phone')}").execute()
    
    if not result.data:
        return jsonify({"status": "not_found", "message": "Aluno não encontrado."})
    
    student = result.data[0]
    has_pin = student.get('pin_hash') is not None
    
    return jsonify({
        "status": "found",
        "has_pin": has_pin,
        "name": student['name']
    })

@students_bp.route('/api/auth/setup-pin', methods=['POST'])
def setup_pin():
    data = request.json
    phone = format_phone(data.get('phone'))
    pin = data.get('pin')
    
    if not phone or not pin or len(pin) != 4:
        return jsonify({"error": "Telefone e PIN de 4 dígitos são obrigatórios"}), 400

    # Verificar se o aluno existe pelo telefone ou whatsapp
    result = supabase.table('students').select('*').or_(f"phone_auth.eq.{phone},whatsapp.eq.{data.get('phone')}").execute()
    
    if not result.data:
        return jsonify({"error": "Aluno não encontrado. Entre em contato com seu treinador."}), 404
    
    student = result.data[0]
    
    # Atualizar phone_auth e pin_hash
    supabase.table('students').update({
        'phone_auth': phone,
        'pin_hash': hash_pin(pin)
    }).eq('id', student['id']).execute()
    
    return jsonify({"status": "success", "message": "PIN configurado com sucesso!"})

@students_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    phone = format_phone(data.get('phone'))
    pin = data.get('pin')
    
    if not phone or not pin:
        return jsonify({"error": "Telefone e PIN são obrigatórios"}), 400

    result = supabase.table('students').select('*').eq('phone_auth', phone).execute()
    
    if not result.data:
        return jsonify({"error": "Credenciais inválidas"}), 401
    
    student = result.data[0]
    
    if not verify_pin(pin, student.get('pin_hash')):
        return jsonify({"error": "Credenciais inválidas"}), 401
    
    # Por enquanto, retornamos os dados do aluno e o access_token antigo para compatibilidade
    return jsonify({
        "status": "success",
        "student": {
            "id": student['id'],
            "name": student['name'],
            "access_token": student['access_token']
        }
    })
