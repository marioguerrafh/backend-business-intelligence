# Omie Provider

## Escopo

Provider do Integration Hub com consumo resiliente aderente as regras oficiais da Omie.

## Capacidades

- `authenticate`
- `health`
- `sync_customers`
- `sync_products`
- `sync_suppliers`
- `sync_sales`
- `sync_accounts_receivable`
- `sync_accounts_payable`
- `sync_cashflow`
- `sync_inventory`
- `sync_hr`
- `full_sync`
- `incremental_sync`
- `disconnect`

## Limites Oficiais Aplicados

- Limite por IP: `960 req/min`.
- Limite por `(IP + APP_KEY + METODO)`: `240 req/min`.
- Concorrrencia maxima por `(IP + APP_KEY + METODO)`: `4` chamadas simultaneas.

Implementacao:

- `OmieRateLimiter` com janela deslizante de 60 segundos.
- `WorkerPool` com fila FIFO e controle por chave de metodo.

## Paginacao

- Todos endpoints de listagem executam paginacao automatica.
- Fluxo:
	- `pagina = 1`
	- consulta pagina
	- persiste
	- `pagina += 1`
	- encerra quando nao ha proxima pagina
- Retry e aplicado por pagina, sem reiniciar endpoint inteiro.

Campos registrados por pagina:

- metodo
- pagina atual
- total de paginas (quando disponivel)
- tempo
- retries
- quantidade importada

## Tamanho de Pagina

- `page_size` e normalizado automaticamente para o maximo suportado configurado em `provider_config.yaml` (`page_size_max`).
- Se o valor solicitado exceder o limite, o provider ajusta automaticamente.

## Sincronizacao Incremental

- Usa `last_success_sync` quando disponivel no vinculo da integracao.
- Fallback para `period_ref` quando nao existir historico.
- `last_success_sync` so e atualizado apos sincronizacao completa com sucesso.

## Cache

- Cache local com TTL configuravel (`cache_ttl_seconds`, default `60`).
- Chave de cache baseada em URL + payload (hash deterministico).
- Evita chamadas repetidas para o mesmo recurso dentro da janela de TTL.

## Retry e Backoff

- Retry somente para falhas transientes (`425`, `429`, `500`, `503`, erros de rede).
- Backoff exponencial configuravel (`1s`, `2s`, `4s`, `8s`, ...).
- Suporte a `Retry-After` quando presente.

## Circuit Breaker

- Estados: `closed`, `open`, `half_open`.
- Abre apos limiar configuravel de falhas consecutivas.
- Respeita timeout de recuperacao.
- Half-open reabre somente apos sucesso.

## Tratamento HTTP 425

- `425` bloqueia temporariamente novas chamadas do metodo afetado.
- Bloqueio com cooldown configuravel (`http_425_cooldown_seconds`) e/ou `Retry-After`.
- Retomada automatica apos cooldown, sem loop infinito (limitada por politica de retry).

## Timeouts

Timeouts configuraveis por provider:

- `connection_timeout`
- `read_timeout`
- `write_timeout`

## Idempotencia

Idempotencia preservada por:

- `company_id`
- `provider`
- `source_record_id`

Nao ha duplicacao de registros no destino quando o mesmo dado e reprocessado.

## Logs e Observabilidade

Logs por pagina incluem:

- provider
- metodo
- pagina
- tempo
- status
- retries
- rate limit remaining (quando disponivel)
- quantidade importada

Metricas em runtime:

- `requests_total`
- `requests_success`
- `requests_failed`
- `retry_total`
- `cache_hits`
- `cache_miss`
- `avg_latency_ms`
- `pages_processed`
- `records_imported`
- `records_failed`
- `rate_limit_waits`

## Health

Endpoint:

- `GET /v1/integrations/health`

Retorna por provider:

- status
- ultima sincronizacao
- ultimo erro
- latencia media
- fila (`in_flight`, `queued`)
- estado do circuit breaker
- metricas de consumo

## Configuracao

Arquivo:

- `backend/provider_config.yaml`

Exemplo:

```yaml
omie:
	max_requests_per_minute_ip: 960
	max_requests_per_method: 240
	max_parallel_requests: 4
	page_size_max: 500
	cache_ttl_seconds: 60
	retry_attempts: 5
	backoff_base_seconds: 1
	backoff_max_seconds: 16
	connection_timeout: 30
	read_timeout: 60
	write_timeout: 30
	circuit_breaker_threshold: 5
	circuit_breaker_timeout: 300
	http_425_cooldown_seconds: 60
```

## Pipeline

Ao finalizar ingest de cada template:

1. publica `ingest.completed.v1`
2. invoca o Pipeline Coordinator existente

Nenhuma alteracao foi feita no Pipeline Orchestrator.

## Boas Praticas Operacionais

- Nao executar full sync concorrente para o mesmo provider/tenant.
- Manter `page_size` dentro do limite automatico do provider.
- Evitar retentativas manuais imediatas apos 425/429.
- Monitorar `retry_total`, `rate_limit_waits` e `avg_latency_ms` para ajuste fino.
