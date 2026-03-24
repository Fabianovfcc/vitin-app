from main import app

print("--- ROTAS REGISTRADAS NO FLASK ---")
for rule in app.url_map.iter_rules():
    print(f"Rota: {rule.rule} | Métodos: {rule.methods} | Endpoint: {rule.endpoint}")
