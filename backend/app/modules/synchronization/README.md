# Synchronization Orchestration Module

## Overview

Este módulo implementa um sistema de orquestração inteligente para sincronizações de dados de provedores externos (Omie, SAP, TOTVS, Conta Azul, Bling, Tiny, etc.).

## Features

✅ **Sincronização por Domínio** - Jobs independentes por domínio (clientes, produtos, vendas, etc.)  
✅ **Checkpoints** - Recuperação automática a partir do último ponto em caso de falha  
✅ **Janelas Temporais** - Particionamento inteligente de dados em períodos gerenciáveis  
✅ **Scheduler Inteligente** - Execução automática com frequências configuráveis  
✅ **Fila com Prioridades** - CRITICAL, HIGH, NORMAL, LOW  
✅ **Worker Pool** - Execução concorrente com thread pool  
✅ **Pipeline Único** - Execução de pipeline apenas após conclusão de todos os jobs  
✅ **Métricas** - Tracking de jobs, registros, duração, etc.  

## Architecture

```
synchronization/
├── domain/                 # Entidades e Value Objects
│   ├── entities.py        # SyncJob, SyncCheckpoint, TimeWindow, SyncBatch
│   └── value_objects.py   # JobStatus, JobPriority, SyncDomain
├── application/           # Casos de uso
│   ├── orchestrator.py   # Coordenação principal
│   ├── scheduler.py      # Agendamento automático
│   └── job_dispatcher.py # Despacho para providers
├── infrastructure/        # Implementações
│   ├── repositories.py   # CheckpointRepository, JobRepository
│   ├── window_manager.py # Gerenciamento de janelas
│   ├── sync_runtime.py   # Métricas e estado
│   ├── worker_pool.py    # Thread pool
│   └── container.py      # Injeção de dependências
└── interfaces/            # API REST
    └── api/
        ├── routes.py     # Endpoints FastAPI
        └── schemas.py    # Schemas Pydantic
```

## Quick Start

### 1. Run Database Migration

```sql
-- Execute: migrations/2026-07-24-001-create-sync-tables.sql
psql -U user -d database -f migrations/2026-07-24-001-create-sync-tables.sql
```

### 2. Configure Domains

Edit `backend/synchronization.yaml`:

```yaml
sales:
  frequency: 15m
  window_days: 7
  priority: high
  enabled: true

customers:
  frequency: daily
  window_days: 3650
  priority: low
  enabled: true
```

### 3. Start Orchestrator

```python
from app.modules.synchronization.infrastructure.container import (
    get_orchestrator,
    get_scheduler
)

# Start orchestrator
orchestrator = get_orchestrator()
orchestrator.start()

# Start scheduler
scheduler = get_scheduler()
scheduler.start()
```

### 4. Schedule a Sync

```python
batch = orchestrator.schedule_full_sync(
    company_id="company-1",
    provider="omie",
    domains=[SyncDomain.CUSTOMERS, SyncDomain.SALES],
    encrypted_credentials=creds,
)

print(f"Batch {batch.batch_id} created with {len(batch.jobs)} jobs")
```

## API Endpoints

- `GET /v1/synchronization/health` - Health status
- `GET /v1/synchronization/jobs` - List jobs
- `GET /v1/synchronization/jobs/{job_id}` - Get job details
- `POST /v1/synchronization/jobs/{job_id}/pause` - Pause job
- `POST /v1/synchronization/jobs/{job_id}/cancel` - Cancel job
- `GET /v1/synchronization/checkpoints` - List checkpoints
- `GET /v1/synchronization/runtime` - Runtime metrics
- `GET /v1/synchronization/scheduler/status` - Scheduler status
- `POST /v1/synchronization/scheduler/start` - Start scheduler
- `POST /v1/synchronization/scheduler/stop` - Stop scheduler

## Testing

```bash
# Run unit tests
pytest tests/unit/synchronization/ -v

# Run all tests
pytest tests/ -v
```

## Documentation

Complete documentation available at: [backend/docs/synchronization-orchestrator.md](../../docs/synchronization-orchestrator.md)

## Key Benefits

### Before (Monolithic)
❌ Single job for all domains  
❌ Failure stops everything  
❌ Always restart from zero  
❌ Doesn't scale  

### After (Orchestrated)
✅ Independent jobs per domain  
✅ Isolated failures  
✅ Checkpoint recovery  
✅ Scales to millions of records  
✅ Respects API limits  
✅ Intelligent scheduling  

## License

Internal use only - Business Intelligence SaaS Platform
