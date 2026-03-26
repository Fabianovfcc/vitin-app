from backend.supabase_client import supabase

def get_tokens():
    print("Recuperando tokens dos alunos...")
    response = supabase.table('students').select('name, access_token').execute()
    for student in response.data:
        print(f"Aluno: {student['name']} | Token: {student['access_token']}")

if __name__ == '__main__':
    get_tokens()
