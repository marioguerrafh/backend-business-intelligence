import requests

# Testar endpoint de health
try:
    print("Testando: http://localhost:8000/v1/synchronization/health")
    response = requests.get("http://localhost:8000/v1/synchronization/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("\n✅ SUCESSO!")
except Exception as e:
    print(f"❌ ERRO: {e}")

# Executar migration
try:
    print("\n" + "="*60)
    print("Executando migration...")
    response = requests.post("http://localhost:8000/v1/admin/run-sync-migration")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("\n✅ MIGRATION EXECUTADA!")
except Exception as e:
    print(f"❌ ERRO: {e}")
