import requests

BASE_URL = "http://127.0.0.1:5000"
TOKEN = "master_vitin_2024"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def test_api():
    print(f"Testando conexão com {BASE_URL}...")
    try:
        # 1. Testar Stats
        r = requests.get(f"{BASE_URL}/api/super/stats", headers=HEADERS)
        print(f"GET /stats -> Status: {r.status_code} | Resposta: {r.text[:100]}")
        
        # 2. Testar Trainers
        r = requests.get(f"{BASE_URL}/api/super/trainers-detailed", headers=HEADERS)
        print(f"GET /trainers-detailed -> Status: {r.status_code} | Resposta: {r.text[:100]}")
        
    except Exception as e:
        print(f"Erro ao conectar: {e}")

if __name__ == "__main__":
    test_api()
