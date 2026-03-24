import os
from flask import Flask, send_from_directory
from dotenv import load_dotenv

# Importar Blueprints e Funções de Núcleo
from backend.database import init_db
from backend.routes_students import students_bp
from backend.routes_workouts import workouts_bp
from backend.routes_admin import admin_bp
from backend.routes_catalog import catalog_bp
from backend.routes_feed import feed_bp
from backend.routes_super_admin import super_admin_bp

load_dotenv()

# O static_folder agora é 'frontend' pois o main.py está na raiz do projeto
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
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/aluno')
def aluno():
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/aluno/<token>')
def aluno_direto(token):
    return send_from_directory(app.static_folder, 'aluno.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# ────────────────────────────────────────
# INICIALIZAÇÃO
# ────────────────────────────────────────
if __name__ == '__main__':
    # Inicializar Banco de Dados
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"App Vitin 2.0 Iniciando na porta {port}...")
    app.run(host="0.0.0.0", port=port)
