# 🚀 Guia Rápido: Testar Omie AGORA

## Passo 1: Executar Migration

```powershell
# Conectar no PostgreSQL
psql -U postgres -d bi_database

# OU se usar outro usuário/banco:
# psql -U seu_usuario -d seu_banco

# Dentro do psql, executar:
\i d:/Projetos/business-intelligence/backend/migrations/2026-07-24-001-create-sync-tables.sql

# Verificar se tabelas foram criadas:
\dt sync_*

# Sair:
\q
```

**Resultado esperado:**
```
           List of relations
 Schema |      Name       | Type  | Owner
--------+-----------------+-------+-------
 public | sync_checkpoints| table | postgres
 public | sync_jobs       | table | postgres
```

---

## Passo 2: Iniciar Servidor

```powershell
cd d:\Projetos\business-intelligence\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Aguarde ver:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Passo 3: Testar Health (sem autenticação)

Abra seu navegador ou Postman:

```
http://localhost:8000/api/v1/synchronization/health
```

**Deve retornar:**
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
    "active_jobs": 0
  }
}
```

✅ **Se retornou isso, está funcionando!**

---

## Passo 4: Iniciar Scheduler

```
POST http://localhost:8000/api/v1/synchronization/scheduler/start
```

**Resposta:**
```json
{
  "status": "started"
}
```

---

## Passo 5: Verificar Status do Scheduler

```
GET http://localhost:8000/api/v1/synchronization/scheduler/status
```

**Deve mostrar domínios configurados e frequências:**
```json
{
  "enabled_domains": ["customers", "products", "sales", ...],
  "schedules": {
    "sales": {
      "frequency_minutes": 15,
      "last_run": null,
      "next_run": "2026-07-24T10:15:00"
    }
  }
}
```

---

## Passo 6: Obter Credenciais Omie (COM autenticação)

**Primeiro, faça login e obtenha token:**
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "seu_email",
  "password": "sua_senha"
}
```

**Copie o token da resposta.**

**Depois, obtenha integração Omie:**
```bash
GET http://localhost:8000/api/v1/integrations
Authorization: Bearer SEU_TOKEN_AQUI
```

**Se não tiver integração Omie, crie:**
```bash
POST http://localhost:8000/api/v1/integrations/connect
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "provider": "omie",
  "credentials": {
    "app_key": "seu_app_key_omie",
    "app_secret": "seu_app_secret_omie"
  }
}
```

**Copie:**
- `company_id` da resposta
- `id` da integração (você vai precisar buscar encrypted_credentials)

---

## Passo 7: Agendar Sync de Vendas dos Últimos 7 Dias

```bash
POST http://localhost:8000/api/v1/synchronization/schedule/domain
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "company_id": "SEU_COMPANY_ID",
  "provider": "omie",
  "domain": "sales",
  "encrypted_credentials": "CREDENCIAIS_CRIPTOGRAFADAS",
  "mode": "incremental",
  "priority": "high",
  "start_date": "2026-07-17",
  "end_date": "2026-07-24"
}
```

**Resposta:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "domain": "sales",
  "priority": "high",
  "created_at": "2026-07-24T10:00:00"
}
```

**Copie o `job_id`!**

---

## Passo 8: Monitorar Job

```bash
GET http://localhost:8000/api/v1/synchronization/jobs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer SEU_TOKEN_AQUI
```

**Status durante execução:**
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

**Status após conclusão:**
```json
{
  "status": "completed",
  "domain": "sales",
  "records_imported": 1485,
  "records_failed": 15,
  "duration_seconds": 145.5,
  "completed_at": "2026-07-24T10:02:30"
}
```

---

## Passo 9: Listar Todos os Jobs

```bash
GET http://localhost:8000/api/v1/synchronization/jobs?company_id=SEU_COMPANY_ID
Authorization: Bearer SEU_TOKEN_AQUI
```

---

## Passo 10: Ver Métricas

```bash
GET http://localhost:8000/api/v1/synchronization/runtime
Authorization: Bearer SEU_TOKEN_AQUI
```

**Resposta:**
```json
{
  "scheduler_running": true,
  "active_jobs": 0,
  "metrics": {
    "global": {
      "jobs_total": 1,
      "jobs_completed": 1,
      "records_imported": 1485,
      "avg_duration_seconds": 145.5
    },
    "per_domain": {
      "sales": {
        "jobs_completed": 1,
        "records_imported": 1485
      }
    }
  }
}
```

---

## 🎉 Pronto!

Você testou:
- ✅ Migration do banco
- ✅ Health do orchestrator
- ✅ Scheduler iniciado
- ✅ Job de sync criado
- ✅ Monitoramento de job
- ✅ Métricas de runtime

---

## Próximos Testes

1. **Testar Full Sync:**
   - Ver: [TESTE_OMIE_SYNC.md](TESTE_OMIE_SYNC.md) seção 8

2. **Testar Checkpoints:**
   - Ver: [TESTE_OMIE_SYNC.md](TESTE_OMIE_SYNC.md) seção 9

3. **Testar Recuperação de Falha:**
   - Ver: [TESTE_OMIE_SYNC.md](TESTE_OMIE_SYNC.md) seção 10

4. **Usar Script Python:**
   ```powershell
   python scripts/test_omie_sync.py
   ```

---

## Troubleshooting Rápido

### ❌ "Table sync_jobs does not exist"
**Solução:** Execute a migration (Passo 1)

### ❌ "Connection refused"
**Solução:** Inicie o servidor (Passo 2)

### ❌ "401 Unauthorized"
**Solução:** Faça login e use o token (Passo 6)

### ❌ Job fica "pending" muito tempo
**Verificar:**
```bash
GET http://localhost:8000/api/v1/synchronization/health
```
Se `worker_pool.running = false`, reinicie o servidor.

---

## Documentação Completa

- [TESTE_OMIE_SYNC.md](TESTE_OMIE_SYNC.md) - Guia completo com todos os endpoints
- [synchronization-orchestrator.md](synchronization-orchestrator.md) - Arquitetura e conceitos
- [README.md](../app/modules/synchronization/README.md) - Quick start do módulo
