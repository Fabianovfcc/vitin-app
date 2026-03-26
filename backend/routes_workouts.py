from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from .supabase_client import supabase

workouts_bp = Blueprint('workouts', __name__)

@workouts_bp.route('/api/workouts', methods=['POST'])
def save_workout():
    try:
        data = request.get_json()
        student_id_raw = data.get('student_id')
        if not student_id_raw:
            return jsonify({"error": "student_id missing"}), 400
            
        student_id = int(student_id_raw)
        student_name = data.get('student_name', '')
        workout_json = data
        date = data.get('date')
        now = datetime.now().isoformat()
        
        print(f"DEBUG: Salvando treino para aluno {student_id} ({student_name})")
        
        # Buscar se já existe para fazer update manual se o upsert falhar por falta de constraint
        existing = supabase.table('workouts').select('id').eq('student_id', student_id).execute()
        
        if existing.data:
            row_id = existing.data[0]['id']
            supabase.table('workouts').update({
                'workout_json': workout_json,
                'date': date,
                'updated_at': now
            }).eq('id', row_id).execute()
        else:
            supabase.table('workouts').insert({
                'student_id': student_id,
                'workout_json': workout_json,
                'date': date,
                'updated_at': now
            }).execute()
        
        supabase.table('students').update({'last_workout': date}).eq('id', student_id).execute()
        supabase.table('workout_progress').delete().eq('student_id', student_id).execute()

        supabase.table('notifications').insert({
            'target_role': 'aluno',
            'student_id': student_id,
            'student_name': student_name,
            'message': 'Seu Personal atualizou sua ficha de treino!',
            'type': 'workout_updated',
            'created_at': now
        }).execute()

        return jsonify({"status": "success", "message": "Treino enviado com sucesso!"}), 201
    except Exception as e:
        print(f"ERRO CRÍTICO ao salvar treino: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@workouts_bp.route('/api/workouts/history')
def get_workout_history():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id missing"}), 400
    
    result = supabase.table('workout_history').select('*').eq(
        'student_id', int(student_id)
    ).order('finished_at', desc=True).execute()
    
    # Mapear campos para compatibilidade com frontend
    history = []
    for h in result.data:
        h['date'] = h.get('finished_at')
        h['created_at'] = h.get('finished_at')
        history.append(h)
    return jsonify(history)

@workouts_bp.route('/api/workouts/<int:student_id>')
def get_workout(student_id):
    result = supabase.table('workouts').select('*').eq('student_id', student_id).execute()
    if result.data:
        row = result.data[0]
        data = row['workout_json'] if isinstance(row['workout_json'], dict) else json.loads(row['workout_json'])
        data['updated_at'] = row['updated_at']
        return jsonify(data)
    return jsonify({"error": "Nenhum treino encontrado"}), 404

@workouts_bp.route('/api/progress/<int:student_id>/<day>', methods=['GET', 'POST'])
def handle_progress(student_id, day):
    now = datetime.now().isoformat()
    if request.method == 'POST':
        data = request.get_json()
        completed_json = data.get('completedSets', {})
        supabase.table('workout_progress').upsert({
            'student_id': student_id,
            'day': day,
            'completed_sets_json': completed_json,
            'updated_at': now
        }).execute()
        return jsonify({"status": "saved"})
    
    result = supabase.table('workout_progress').select('*').eq(
        'student_id', student_id
    ).eq('day', day).execute()
    
    if result.data:
        return jsonify(result.data[0]['completed_sets_json'])
    return jsonify({})

@workouts_bp.route('/api/workouts/finish', methods=['POST'])
def finish_workout():
    data = request.get_json()
    student_id = data.get('student_id')
    student_name = data.get('student_name', 'Aluno')
    day = data.get('day', '')
    total_sets = data.get('total_sets', 0)
    completed_sets = data.get('completed_sets', 0)
    cardio = data.get('cardio', '')
    completed_sets_json = data.get('completed_sets_json', {})
    calories = data.get('calories', completed_sets * 5)
    now = datetime.now().isoformat()
    
    supabase.table('workout_history').insert({
        'student_id': student_id,
        'student_name': student_name,
        'day': day,
        'total_sets': total_sets,
        'completed_sets': completed_sets,
        'cardio': cardio,
        'completed_sets_json': completed_sets_json,
        'calories': calories,
        'finished_at': now
    }).execute()
    
    pct = round((completed_sets / total_sets * 100)) if total_sets > 0 else 0
    msg = f'{student_name} finalizou o treino de {day.upper()} ({pct}% completo)'
    if cardio: msg += f' + Cardio: {cardio}'
    
    supabase.table('notifications').insert({
        'target_role': 'professor',
        'student_id': student_id,
        'student_name': student_name,
        'message': msg,
        'type': 'workout_finished',
        'created_at': now
    }).execute()
    
    return jsonify({"status": "success", "message": "Treino finalizado!"}), 201
