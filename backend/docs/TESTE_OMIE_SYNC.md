# Como Testar Sincronização Omie com Orchestrator

## 1. Executar Migration do Banco de Dados

```powershell
# Conectar no PostgreSQL e executar migration
cd d:\Projetos\business-intelligence\backend
psql -U postgres -d bi_database -f migrations/2026-07-24-001-create-sync-tables.sql
```

**OU usando pgAdmin:**
1. Abrir pgAdmin
2. Conectar no banco `bi_database`
3. Abrir Query Tool
4. Carregar e executar `migrations/2026-07-24-001-create-sync-tables.sql`

---

## 2. Iniciar o Servidor FastAPI

```powershell
cd d:\Projetos\business-intelligence\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Verificar Health do Orchestrator

```bash
GET http://localhost:8000/api/v1/synchronization/health
```

**Resposta esperada:**
```json
{
  "orchestrator": "running",
  "worker_pool": {
    "running": true,
    "queue_size": 0,
    "max_workers": 4
  },
  "runtime": {
    "scheduler_running": false,
    "active_jobs": 0,
    "metrics": {
      "global": {
        "jobs_total": 0,
        "jobs_completed": 0,
        "jobs_failed": 0,
        "records_imported": 0
      }
    }
  }
}
```

---

## 4. Iniciar o Scheduler

```bash
POST http://localhost:8000/api/v1/synchronization/scheduler/start
```

**Resposta esperada:**
```json
{
  "status": "started"
}
```

---

## 5. Verificar Status do Scheduler

```bash
GET http://localhost:8000/api/v1/synchronization/scheduler/status
```

**Resposta esperada:**
```json
{
  "enabled_domains": ["customers", "products", "sales", ...],
  "schedules": {
    "sales": {
      "frequency_minutes": 15,
      "last_run": null,
      "next_run": "2026-07-24T10:15:00",
      "seconds_until_next": 900
    }
  }
}
```

---

## 6. Testar Sincronização Manual de Vendas (Sales)

### 6.1. Obter Credenciais Omie da Empresa

```bash
GET http://localhost:8000/api/v1/integrations
Authorization: Bearer {seu_token}
```

Você precisa ter uma integração Omie configurada. Se não tiver, configure primeiro:

```bash
POST http://localhost:8000/api/v1/integrations/connect
Authorization: Bearer {seu_token}
Content-Type: application/json

{
  "provider": "omie",
  "credentials": {
    "app_key": "seu_app_key_omie",
    "app_secret": "seu_app_secret_omie"
  }
}
```

### 6.2. Agendar Sincronização de Vendas dos Últimos 7 Dias

**Usando cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/synchronization/schedule/domain \
  -H "Authorization: Bearer {seu_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "sua_company_id",
    "provider": "omie",
    "domain": "sales",
    "encrypted_credentials": "{credenciais_criptografadas}",
    "mode": "incremental",
    "priority": "high",
    "start_date": "2026-07-17",
    "end_date": "2026-07-24"
  }'
```

**Usando Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/synchronization/schedule/domain",
    headers={
        "Authorization": f"Bearer {seu_token}",
        "Content-Type": "application/json"
    },
    json={
        "company_id": "sua_company_id",
        "provider": "omie",
        "domain": "sales",
        "encrypted_credentials": credenciais_criptografadas,
        "mode": "incremental",
        "priority": "high",
        "start_date": "2026-07-17",
        "end_date": "2026-07-24"
    }
)

job = response.json()
print(f"Job ID: {job['job_id']}")
print(f"Status: {job['status']}")
```

**Resposta esperada:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "sua_company_id",
  "provider": "omie",
  "domain": "sales",
  "status": "pending",
  "priority": "high",
  "mode": "incremental",
  "window_start": "2026-07-17",
  "window_end": "2026-07-24",
  "created_at": "2026-07-24T10:00:00"
}
```

---

## 7. Monitorar o Job

### 7.1. Obter Status do Job

```bash
GET http://localhost:8000/api/v1/synchronization/jobs/{job_id}
Authorization: Bearer {seu_token}
```

**Resposta (em execução):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "domain": "sales",
  "started_at": "2026-07-24T10:00:05",
  "records_read": 150,
  "records_imported": 145,
  "pages_processed": 3
}
```

**Resposta (concluído):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "domain": "sales",
  "started_at": "2026-07-24T10:00:05",
  "completed_at": "2026-07-24T10:02:30",
  "duration_seconds": 145.5,
  "records_read": 1500,
  "records_imported": 1485,
  "records_failed": 15,
  "pages_processed": 30
}
```

### 7.2. Listar Todos os Jobs

```bash
GET http://localhost:8000/api/v1/synchronization/jobs?company_id=sua_company_id
Authorization: Bearer {seu_token}
```

### 7.3. Listar Jobs por Domínio

```bash
GET http://localhost:8000/api/v1/synchronization/jobs?company_id=sua_company_id&domain=sales
Authorization: Bearer {seu_token}
```

### 7.4. Listar Jobs por Status

```bash
GET http://localhost:8000/api/v1/synchronization/jobs?status=running
Authorization: Bearer {seu_token}
```

---

## 8. Testar Full Sync (Todos os Domínios)

```python
import requests
from datetime import date, timedelta

# Últimos 30 dias para vendas, últimos 10 anos para clientes/produtos
today = date.today()
sales_start = today - timedelta(days=30)

response = requests.post(
    "http://localhost:8000/api/v1/synchronization/schedule/full",
    headers={
        "Authorization": f"Bearer {seu_token}",
        "Content-Type": "application/json"
    },
    json={
        "company_id": "sua_company_id",
        "provider": "omie",
        "domains": ["customers", "products", "sales"],
        "encrypted_credentials": credenciais_criptografadas,
        "window_config": {
            "customers": 3650,  # 10 anos em janela única
            "products": 3650,   # 10 anos em janela única
            "sales": 7          # 7 dias por janela
        },
        "priority_config": {
            "customers": "low",
            "products": "low",
            "sales": "high"
        }
    }
)

batch = response.json()
print(f"Batch ID: {batch['batch_id']}")
print(f"Total Jobs: {batch['total_jobs']}")
for job in batch['jobs']:
    print(f"  - {job['domain']}: {job['status']}")
```

---

## 9. Verificar Checkpoints

Checkpoints permitem recuperação em caso de falha:

```bash
GET http://localhost:8000/api/v1/synchronization/checkpoints?company_id=sua_company_id&domain=sales
Authorization: Bearer {seu_token}
```

**Resposta:**
```json
{
  "total": 1,
  "checkpoints": [
    {
      "checkpoint_id": "cp-123",
      "domain": "sales",
      "status": "active",
      "last_page": 15,
      "last_window_start": "2026-07-17",
      "last_window_end": "2026-07-24",
      "last_success_sync": "2026-07-24T10:02:30"
    }
  ]
}
```

---

## 10. Testar Recuperação de Falha

Se um job falhar, o sistema cria um checkpoint. Para retomar:

```python
# O próximo agendamento do mesmo domínio automaticamente retoma do checkpoint
response = requests.post(
    "http://localhost:8000/api/v1/synchronization/schedule/domain",
    headers={"Authorization": f"Bearer {seu_token}"},
    json={
        "company_id": "sua_company_id",
        "provider": "omie",
        "domain": "sales",
        "encrypted_credentials": credenciais_criptografadas,
        "mode": "incremental"
    }
)

# O orchestrator detecta checkpoint ativo e retoma da página salva
```

---

## 11. Controlar Jobs

### Pausar Job
```bash
POST http://localhost:8000/api/v1/synchronization/jobs/{job_id}/pause
Authorization: Bearer {seu_token}
```

### Cancelar Job
```bash
POST http://localhost:8000/api/v1/synchronization/jobs/{job_id}/cancel
Authorization: Bearer {seu_token}
```

---

## 12. Verificar Métricas de Runtime

```bash
GET http://localhost:8000/api/v1/synchronization/runtime
Authorization: Bearer {seu_token}
```

**Resposta:**
```json
{
  "scheduler_running": true,
  "active_jobs": 2,
  "metrics": {
    "global": {
      "jobs_total": 150,
      "jobs_completed": 145,
      "jobs_failed": 5,
      "records_imported": 50000,
      "avg_duration_seconds": 32.5
    },
    "per_domain": {
      "sales": {
        "jobs_completed": 50,
        "records_imported": 20000,
        "avg_duration_seconds": 45.2
      },
      "customers": {
        "jobs_completed": 30,
        "records_imported": 15000,
        "avg_duration_seconds": 25.1
      }
    }
  }
}
```

---

## 13. Verificar Logs

Os logs do orchestrator estão em:

```powershell
# Ver logs em tempo real
Get-Content -Path "logs/app.log" -Wait -Tail 50

# Filtrar logs de sync
Get-Content -Path "logs/app.log" | Select-String "synchronization"
```

---

## Troubleshooting

### Problema: "Table sync_jobs does not exist"
**Solução:** Execute a migration do passo 1

### Problema: "No active checkpoint found"
**Normal:** Primeira execução não tem checkpoint

### Problema: Job fica em "pending" indefinidamente
**Verificar:**
1. Worker pool está rodando? Check `/health`
2. Há workers disponíveis? Check `queue_size`
3. Logs têm erros? Check logs

### Problema: "Rate limit exceeded"
**Solução:** O Omie tem limite de 960 req/min por IP. O orchestrator já gerencia isso via janelas temporais. Se ainda ocorrer:
1. Aumentar `window_days` no `synchronization.yaml`
2. Reduzir frequência de execução

---

## Próximos Passos

1. ✅ Testar sync de vendas (sales)
2. ✅ Testar sync de clientes (customers)
3. ✅ Testar full sync
4. ✅ Testar recuperação de falha
5. ✅ Configurar scheduler para produção
6. ✅ Monitorar métricas

---

## Configuração de Produção

Edite `backend/synchronization.yaml`:

```yaml
# Vendas - Alta frequência
sales:
  frequency: 15m
  window_days: 7
  priority: high
  enabled: true
  max_parallel_jobs: 1

# Clientes - Baixa frequência
customers:
  frequency: daily
  window_days: 3650
  priority: low
  enabled: true
  max_parallel_jobs: 1

# Produtos - Baixa frequência
products:
  frequency: daily
  window_days: 3650
  priority: low
  enabled: true
  max_parallel_jobs: 1
```

**Reiniciar scheduler após alterar configuração:**
```bash
POST http://localhost:8000/api/v1/synchronization/scheduler/stop
POST http://localhost:8000/api/v1/synchronization/scheduler/start
```
