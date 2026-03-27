import os
from flask import Flask, send_from_directory, request
from dotenv import load_dotenv

# Importar Blueprints
from backend.routes_students import students_bp
from backend.routes_workouts import workouts_bp
from backend.routes_admin import admin_bp
from backend.routes_catalog import catalog_bp
from backend.routes_feed import feed_bp
from backend.routes_super_admin import super_admin_bp

load_dotenv()
# Carregar .env do backend também
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

app = Flask(__name__, static_folder='frontend')

# Registrar Blueprints
app.register_blueprint(students_bp)
app.register_blueprint(workouts_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(super_admin_bp, url_prefix='/api/super')

# ────────────────────────────────────────
# ROTAS DE PÁGINAS ESTÁTICAS
# ────────────────────────────────────────
@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    # Forçar no-cache para evitar problemas relatados
    if 'api' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    return response

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/aluno')
def aluno():
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/aluno/<token>')
def aluno_direto(token):
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/master')
def master_admin():
    return send_from_directory(app.static_folder, 'super_admin.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# ────────────────────────────────────────
# INICIALIZAÇÃO
# ────────────────────────────────────────
if __name__ == '__main__':
    # Seed Supabase (apenas popula se tabelas estiverem vazias)
    from backend.seed_supabase import seed
    seed()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"App Vitin 2.0 (Supabase) Iniciando na porta {port}...")
    app.run(host="0.0.0.0", port=port)
