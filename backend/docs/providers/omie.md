# Omie Provider

## Escopo

Primeiro provider completo do Integration Hub.

## Capacidades

- authenticate
- health
- sync_customers
- sync_products
- sync_suppliers
- sync_sales
- sync_accounts_receivable
- sync_accounts_payable
- sync_cashflow
- sync_inventory
- sync_hr
- full_sync
- incremental_sync
- disconnect

## Resiliencia

- Retry policy com backoff incremental.
- Timeout validado por credencial.
- Rate limiting por janela de 1 segundo.
- Circuit breaker para falhas consecutivas.

## Mapeamento Canonical

- Customer Aggregate
- Product Aggregate
- fact_sales
- fact_accounts_receivable
- fact_accounts_payable
- fact_cashflow
- fact_inventory
- fact_hr

## Pipeline

Ao finalizar ingest de cada template:

1. publica ingest.completed.v1
2. invoca Pipeline Coordinator existente

## Testabilidade

Provider nao depende de API real nos testes. Usa payload deterministico para garantir cobertura de contract/integration/gate.
