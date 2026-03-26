import requests
import json

BASE_URL = "http://localhost:5000"

def reproduce():
    print("Tentando reproduzir erro 500 ao salvar treino...")
    # Dados que o front-end envia normalmente
    payload = {
        "student_id": 4, # Fabiano Vieira
        "student_name": "Fabiano Vieira",
        "date": "2026-03-26",
        "days": ["seg"],
        "exercises": {
            "seg": [
                {"name": "Supino Reto", "sets": 4, "reps": "12", "load": "50", "obs": ""}
            ]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/workouts", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Erro na requisição: {e}")

if __name__ == '__main__':
    reproduce()
