"""
Script de teste rápido para sincronização Omie com Orchestrator.

Execute: python scripts/test_omie_sync.py
"""
import requests
from datetime import date, timedelta
import json
import time

# Configuração
BASE_URL = "http://localhost:8000/api/v1"
COMPANY_ID = "sua_company_id"  # ALTERE AQUI
TOKEN = "seu_token_aqui"  # ALTERE AQUI

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def check_health():
    """Verificar health do orchestrator."""
    print_section("1. Verificando Health do Orchestrator")
    
    response = requests.get(f"{BASE_URL}/synchronization/health")
    health = response.json()
    
    print(f"✓ Orchestrator: {health['orchestrator']}")
    print(f"✓ Worker Pool: {health['worker_pool']}")
    print(f"✓ Runtime: {health['runtime']}")
    
    return health


def start_scheduler():
    """Iniciar scheduler."""
    print_section("2. Iniciando Scheduler")
    
    response = requests.post(f"{BASE_URL}/synchronization/scheduler/start")
    result = response.json()
    
    print(f"✓ Status: {result.get('status', 'unknown')}")
    
    return result


def get_scheduler_status():
    """Obter status do scheduler."""
    print_section("3. Status do Scheduler")
    
    response = requests.get(f"{BASE_URL}/synchronization/scheduler/status")
    status = response.json()
    
    print(f"Domínios habilitados: {len(status.get('enabled_domains', []))}")
    
    if 'schedules' in status:
        for domain, config in status['schedules'].items():
            freq = config.get('frequency_minutes', 'N/A')
            next_run = config.get('next_run', 'N/A')
            print(f"  - {domain}: a cada {freq} minutos, próximo em {next_run}")
    
    return status


def schedule_sales_sync():
    """Agendar sincronização de vendas dos últimos 7 dias."""
    print_section("4. Agendando Sincronização de Vendas")
    
    # NOTA: Você precisa ter credenciais Omie configuradas
    # Obtenha de GET /api/v1/integrations primeiro
    
    today = date.today()
    start_date = today - timedelta(days=7)
    
    payload = {
        "company_id": COMPANY_ID,
        "provider": "omie",
        "domain": "sales",
        # "encrypted_credentials": "...",  # ADICIONE AQUI
        "mode": "incremental",
        "priority": "high",
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat()
    }
    
    print(f"Período: {start_date} a {today}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Descomente quando tiver credenciais configuradas
    # response = requests.post(
    #     f"{BASE_URL}/synchronization/schedule/domain",
    #     headers=headers,
    #     json=payload
    # )
    # job = response.json()
    # 
    # print(f"\n✓ Job criado!")
    # print(f"  Job ID: {job['job_id']}")
    # print(f"  Status: {job['status']}")
    # print(f"  Domínio: {job['domain']}")
    # 
    # return job
    
    print("\n⚠️  Descomente o código acima quando tiver credenciais configuradas")
    return None


def get_job_status(job_id: str):
    """Obter status de um job."""
    print_section(f"5. Monitorando Job {job_id}")
    
    response = requests.get(
        f"{BASE_URL}/synchronization/jobs/{job_id}",
        headers=headers
    )
    job = response.json()
    
    print(f"Status: {job['status']}")
    print(f"Domínio: {job['domain']}")
    
    if job.get('started_at'):
        print(f"Iniciado em: {job['started_at']}")
    
    if job.get('records_imported'):
        print(f"Registros importados: {job['records_imported']}")
    
    if job.get('completed_at'):
        print(f"Concluído em: {job['completed_at']}")
        print(f"Duração: {job.get('duration_seconds', 0):.2f}s")
    
    return job


def list_jobs():
    """Listar todos os jobs da empresa."""
    print_section("6. Listando Jobs")
    
    response = requests.get(
        f"{BASE_URL}/synchronization/jobs",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    result = response.json()
    
    print(f"Total de jobs: {result['total']}")
    
    for job in result.get('jobs', [])[:5]:  # Mostrar apenas os 5 primeiros
        status_icon = "✓" if job['status'] == "completed" else "⏳"
        print(f"{status_icon} {job['domain']}: {job['status']} - {job.get('records_imported', 0)} registros")
    
    return result


def get_runtime_metrics():
    """Obter métricas de runtime."""
    print_section("7. Métricas de Runtime")
    
    response = requests.get(f"{BASE_URL}/synchronization/runtime")
    metrics = response.json()
    
    print(f"Scheduler rodando: {metrics.get('scheduler_running')}")
    print(f"Jobs ativos: {metrics.get('active_jobs', 0)}")
    
    if 'metrics' in metrics:
        global_metrics = metrics['metrics'].get('global', {})
        print(f"\nMétricas Globais:")
        print(f"  - Total de jobs: {global_metrics.get('jobs_total', 0)}")
        print(f"  - Jobs completados: {global_metrics.get('jobs_completed', 0)}")
        print(f"  - Jobs falhados: {global_metrics.get('jobs_failed', 0)}")
        print(f"  - Registros importados: {global_metrics.get('records_imported', 0)}")
        print(f"  - Duração média: {global_metrics.get('avg_duration_seconds', 0):.2f}s")
    
    return metrics


def main():
    """Executar testes."""
    print("\n" + "🚀 " * 20)
    print("  TESTE DE SINCRONIZAÇÃO OMIE COM ORCHESTRATOR")
    print("🚀 " * 20)
    
    try:
        # 1. Health check
        health = check_health()
        
        # 2. Iniciar scheduler
        start_scheduler()
        
        # 3. Status do scheduler
        get_scheduler_status()
        
        # 4. Agendar sync de vendas
        job = schedule_sales_sync()
        
        # 5. Se job foi criado, monitorar
        if job and 'job_id' in job:
            time.sleep(2)  # Aguardar início
            get_job_status(job['job_id'])
        
        # 6. Listar jobs
        list_jobs()
        
        # 7. Métricas
        get_runtime_metrics()
        
        print_section("✅ Testes Concluídos")
        print("Para mais informações, consulte: docs/TESTE_OMIE_SYNC.md")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao servidor.")
        print("Certifique-se que o FastAPI está rodando:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Verificar configuração
    if COMPANY_ID == "sua_company_id" or TOKEN == "seu_token_aqui":
        print("\n⚠️  ATENÇÃO: Configure COMPANY_ID e TOKEN no início do script!")
        print("Executando testes básicos (sem autenticação)...\n")
    
    main()
