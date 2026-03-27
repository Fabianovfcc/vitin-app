from .supabase_client import supabase
from .auth import require_auth
from flask import Blueprint, jsonify, request, current_app, g

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/exercises', methods=['GET', 'POST'])
@require_auth
def handle_exercises():
    if request.method == 'POST':
        data = request.get_json()
        if 'id' in data:
            supabase.table('exercises').update({
                'name': data['name'], 'category': data['category'], 'image': data['image']
            }).eq('id', data['id']).execute()
        else:
            result = supabase.table('exercises').insert({
                'name': data['name'], 'category': data['category'], 'image': data['image']
            }).execute()
            data['id'] = result.data[0]['id'] if result.data else None
        return jsonify(data)
    
    result = supabase.table('exercises').select('*').execute()
    return jsonify(result.data)

@admin_bp.route('/api/notifications/<role>')
@require_auth
def get_notifications(role):
    # Professores só veem suas notificações
    student_id = request.args.get('student_id')
    query = supabase.table('notifications').select('*').eq('target_role', role)
    
    if role == 'professor' and g.user_role == 'professor':
        query = query.eq('trainer_id', g.user_id)
    if role == 'aluno' and student_id:
        query = query.eq('student_id', student_id)
    result = query.order('created_at', desc=True).limit(20).execute()
    return jsonify(result.data)

@admin_bp.route('/api/notifications/mark-read', methods=['POST'])
@require_auth
def mark_notifications_read():
    data = request.get_json()
    role = data.get('role', '')
    student_id = data.get('student_id')
    query = supabase.table('notifications').update({'is_read': True}).eq('target_role', role)
    if role == 'professor' and g.user_role == 'professor':
        query = query.eq('trainer_id', g.user_id)
    if role == 'aluno' and student_id:
        query = query.eq('student_id', student_id)
    query.execute()
    return jsonify({"status": "ok"})

@admin_bp.route('/api/notifications/unread-count/<role>')
@require_auth
def unread_count(role):
    student_id = request.args.get('student_id')
    try:
        query = supabase.table('notifications').select('id', count='exact').eq('target_role', role).eq('is_read', False)
        if role == 'professor' and g.user_role == 'professor':
            # Tenta filtrar por trainer_id, se a coluna não existir, o try intercepta
            query = query.eq('trainer_id', g.user_id)
        if role == 'aluno' and student_id:
            query = query.eq('student_id', student_id)
        result = query.execute()
        return jsonify({"count": result.count if result.count is not None else 0})
    except Exception as e:
        print(f"Aviso: Tabela notifications pode estar sem trainer_id: {e}")
        # Fallback: busca sem o filtro de isolamento se a coluna falhar
        query = supabase.table('notifications').select('id', count='exact').eq('target_role', role).eq('is_read', False)
        if role == 'aluno' and student_id:
            query = query.eq('student_id', student_id)
        result = query.execute()
        return jsonify({"count": result.count if result.count is not None else 0})

@admin_bp.route('/api/challenges/active', methods=['GET', 'POST', 'DELETE'])
@require_auth
def handle_active_challenge():
    if request.method == 'POST':
        data = request.get_json()
        now = datetime.now().isoformat()
        supabase.table('challenges').update({'active': False}).eq('active', True).execute()
        if data.get('title') and data.get('description'):
            supabase.table('challenges').insert({
                'title': data['title'], 'description': data['description'], 'active': True, 'created_at': now
            }).execute()
        return jsonify({"status": "success"})
    elif request.method == 'DELETE':
        supabase.table('challenges').update({'active': False}).eq('active', True).execute()
        return jsonify({"status": "deleted"})
    
    result = supabase.table('challenges').select('*').eq('active', True).order('id', desc=True).limit(1).execute()
    if result.data:
        return jsonify(result.data[0])
    return jsonify({"active": False}), 404

@admin_bp.route('/api/history/<int:student_id>')
@require_auth
def get_history(student_id):
    result = supabase.table('workout_history').select('*').eq(
        'student_id', student_id
    ).order('finished_at', desc=True).limit(30).execute()
    return jsonify(result.data)

@admin_bp.route('/api/history/recent')
@require_auth
def recent_history():
    if g.user_role == 'professor':
        # Filtrar por alunos do professor
        res_students = supabase.table('students').select('id').eq('trainer_id', g.user_id).execute()
        student_ids = [s['id'] for s in res_students.data]
        if not student_ids:
            return jsonify([])
        result = supabase.table('workout_history').select('*').in_('student_id', student_ids).order('finished_at', desc=True).limit(20).execute()
        return jsonify(result.data)
    
    # Master vê tudo
    result = supabase.table('workout_history').select('*').order('finished_at', desc=True).limit(20).execute()
    return jsonify(result.data)

@admin_bp.route('/api/trainer/profile', methods=['GET', 'POST'])
@require_auth
def handle_trainer_profile():
    if g.user_role != 'professor':
        return jsonify({"error": "Acesso restrito a professores"}), 403
    
    trainer_id = g.user_id
    if request.method == 'POST':
        data = request.get_json()
        supabase.table('trainers').update({
            'name': data['name'], 'cref': data.get('cref'), 
            'specialty': data.get('specialty'), 'bio': data.get('bio', ''), 
            'image': data.get('image', '')
        }).eq('id', trainer_id).execute()
    
    result = supabase.table('trainers').select('*').eq('id', trainer_id).execute()
    if not result.data:
        return jsonify({"error": "Trainer não encontrado"}), 404
    return jsonify(result.data[0])

@admin_bp.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        
        upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        full_path = os.path.join(upload_path, unique_name)
        file.save(full_path)
        
        return jsonify({"url": f"/uploads/{unique_name}"})
    
    return jsonify({"error": "Falha no upload"}), 500

@admin_bp.route('/api/info/ip')
def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "127.0.0.1"
    return jsonify({"ip": ip})
