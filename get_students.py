import sqlite3
import os

# Caminho corrigido para a nova estrutura modular
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'backend', 'data', 'vitin.db')

def get_students():
    if not os.path.exists(DB_PATH):
        print(f"Erro: Banco de dados não encontrado em {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    students = cursor.execute("SELECT id, name, access_token FROM students").fetchall()
    print("\n--- LISTA DE ALUNOS E TOKENS ---")
    for s in students:
        print(f"ID: {s['id']} | Nome: {s['name']} | Token: {s['access_token']}")
        print(f"Link: http://localhost:5000/aluno/{s['access_token']}")
    print("--------------------------------\n")
    conn.close()

if __name__ == "__main__":
    get_students()
