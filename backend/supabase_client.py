"""
Vitin App - Supabase Client
Módulo centralizado de conexão com o Supabase (PostgreSQL + Storage).
Substitui o antigo database.py (SQLite).
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)
load_dotenv()  # Fallback para .env na raiz

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar definidos no .env")

# Usar service_role key para bypass de RLS no backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_supabase() -> Client:
    """Retorna a instância global do cliente Supabase."""
    return supabase
