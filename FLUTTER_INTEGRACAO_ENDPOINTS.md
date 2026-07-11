# Guia de Integracao Flutter com Endpoints

Data: 2026-07-11
Escopo: Integracao do app Flutter com API existente (sem alteracoes de backend)

## 1. Base da API

- Base URL local: http://localhost:8000
- Prefixo v1: /v1
- Health geral: GET /health
- OpenAPI (para validar contratos no app):
  - GET /openapi.json
  - GET /docs

## 2. Autenticacao e Sessao

### 2.1 Login

- Metodo: POST
- URL: /v1/auth/login
- Auth: nao
- Body JSON:

{
  "email": "owner@acme.com",
  "password": "Owner@123",
  "company_id": "cmp_acme"
}

- Response 200:

{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "refresh_expires_in": 10080
}

### 2.2 Refresh Token

- Metodo: POST
- URL: /v1/auth/refresh
- Auth: nao
- Body JSON:

{
  "refresh_token": "..."
}

- Response 200: mesmo contrato de login.

### 2.3 Logout

- Metodo: POST
- URL: /v1/auth/logout
- Auth: opcional (server usa refresh token do body)
- Body JSON:

{
  "refresh_token": "..."
}

- Response 204: sem body.

### 2.4 Usuario logado

- Metodo: GET
- URL: /v1/auth/me
- Auth: sim (Authorization: Bearer <access_token>)
- Response 200:

{
  "user_id": "usr_...",
  "email": "owner@acme.com",
  "company_id": "cmp_acme",
  "roles": ["owner"]
}

## 3. Header padrao para Flutter

Enviar em todas as chamadas autenticadas:

- Authorization: Bearer <access_token>
- X-Correlation-ID: <uuid-gerado-no-app>

Observacao:
- Se retornar 401, executar refresh uma vez e repetir request original.
- Se refresh falhar, limpar sessao local e voltar para Login.

## 4. Endpoints por modulo

## 4.1 Summary (Home e Dashboard Executivo)

### Buscar resumo executivo

- Metodo: GET
- URL: /v1/summary
- Auth: sim
- Query opcional:
  - period_ref=YYYY-MM
  - company_id=cmp_xxx (somente se igual ao tenant do token)

Response 200 (estrutura):

{
  "summary_id": "sum_...",
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "generated_at": "2026-07-11T...Z",
  "scores": {
    "overall": 80.0,
    "financial": 81.0,
    "commercial": 79.0,
    "operational": 78.0
  },
  "kpis": [
    {
      "kpi_id": "FIN-03",
      "name": "fluxo_caixa_operacional",
      "value": -1200.0,
      "unit": "BRL",
      "trend": "down",
      "health": "red"
    }
  ],
  "alerts": [
    {
      "alert_id": "rr_...",
      "severity": "HIGH",
      "priority": "p0",
      "title": "...",
      "description": "..."
    }
  ],
  "insights": [
    {
      "insight_id": "ins_...",
      "type": "executive_summary",
      "statement": "...",
      "evidence": {}
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "rec.cash.001",
      "title": "...",
      "rank": 0.9,
      "expected_impact": {},
      "owner_role": "...",
      "sla_target": "48h"
    }
  ],
  "trends": {
    "today_vs_yesterday": 1.2,
    "today_vs_last_month": 2.1,
    "today_vs_last_year": 4.8
  },
  "next_risks": [],
  "timeline": {
    "points": [
      {
        "snapshot_date": "2026-07-10",
        "overall_score": 80.0,
        "financial_score": 81.0,
        "commercial_score": 79.0,
        "operational_score": 78.0
      }
    ]
  }
}

## 4.2 Importacoes

### Upload CSV

- Metodo: POST
- URL: /v1/imports/csv
- Auth: sim
- Content-Type: multipart/form-data
- Campos:
  - company_id: string
  - template: customers | products | sales | financial
  - source_system: string (opcional; default csv_official_template)
  - file: arquivo .csv

Response 200:

{
  "job_id": "imp_...",
  "template": "sales",
  "status": "success",
  "total_rows": 120,
  "imported_rows": 120,
  "failed_rows": 0,
  "ingest_event_id": "evt_...",
  "inconsistencies": []
}

## 4.3 Business (cadastros)

### Upsert Customer

- Metodo: POST
- URL: /v1/business/customers
- Auth: sim
- Body JSON: conforme contrato de UpsertCustomerRequest
- Response: CustomerResponse

### Get Customer

- Metodo: GET
- URL: /v1/business/customers/{company_id}/{customer_id}
- Auth: sim
- Response: CustomerResponse

### Upsert Product

- Metodo: POST
- URL: /v1/business/products
- Auth: sim
- Body JSON: conforme contrato de UpsertProductRequest
- Response: ProductResponse

### Get Product

- Metodo: GET
- URL: /v1/business/products/{company_id}/{product_id}
- Auth: sim
- Response: ProductResponse

## 4.4 Pipelines internos (orquestracao de dados)

Observacao importante:
- Estes endpoints estao sob /internal e sao para pipeline/orquestracao.
- O app Flutter pode consumir em ambiente interno/admin, mas para UX comum prefira ler Summary.

### KPI Formula Evaluate

- POST /v1/kpi/internal/formulas/evaluate
- Body:

{
  "formula_id": "f.fin03",
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "metrics": {}
}

### KPI Orchestrator (ingest completed)

- POST /v1/kpi/internal/orchestrator/ingest-completed
- Body:

{
  "company_id": "cmp_acme",
  "import_job_id": "imp_001",
  "template": "sales",
  "source_system": "csv_official_template",
  "event_id": "evt_ing_1",
  "orchestrator_run_id": "run_orc_1",
  "period_ref": "2026-07",
  "correlation_id": "corr_1"
}

### Rule Engine

- POST /v1/rule/internal/execute
- Body:

{
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "orchestrator_run_id": "run_rule_1",
  "source_event_id": "evt_...",
  "correlation_id": "corr_1"
}

### Recommendation Engine

- POST /v1/recommendation/internal/generate
- Body:

{
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "orchestrator_run_id": "run_rec_1",
  "source_event_id": "evt_...",
  "correlation_id": "corr_1"
}

### Insight Engine

- POST /v1/insight/internal/generate
- Body:

{
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "orchestrator_run_id": "run_ins_1",
  "source_event_id": "evt_...",
  "correlation_id": "corr_1"
}

### Executive Score Engine

- POST /v1/executive-score/internal/calculate
- Body:

{
  "company_id": "cmp_acme",
  "period_ref": "2026-07",
  "orchestrator_run_id": "run_exec_1",
  "source_event_id": "evt_...",
  "correlation_id": "corr_1"
}

## 5. Mapeamento por tela Flutter

- Splash:
  - GET /health
  - validacao de sessao local (token salvo)
- Login:
  - POST /v1/auth/login
- Home:
  - GET /v1/summary?period_ref=<mes_atual>
- Dashboard Executivo:
  - GET /v1/summary?period_ref=<selecionado>
- KPIs:
  - GET /v1/summary e usar lista summary.kpis
- Alertas:
  - GET /v1/summary e usar lista summary.alerts
- Recomendacoes:
  - GET /v1/summary e usar lista summary.recommendations
- Insights:
  - GET /v1/summary e usar lista summary.insights
- Timeline:
  - GET /v1/summary e usar summary.timeline.points
- Empresa:
  - Sem endpoint dedicado no momento; usar dados de tenant de /v1/auth/me + dados de negocio disponiveis no fluxo atual
- Perfil:
  - GET /v1/auth/me
- Configuracoes:
  - Sem endpoint dedicado no momento (implementar local-first no app ate API dedicada)
- Importacoes:
  - POST /v1/imports/csv
- Historico de Importacoes:
  - Endpoint dedicado nao exposto neste momento
  - alternativa atual: manter historico local por job_id e status retornado no upload

## 6. Estrategia de estados no app

- Loading:
  - Exibir skeleton para Home/Dashboard com timeout de 10s
- Empty:
  - Se summary retornar 404, exibir estado sem dados + CTA para Importacoes
- Error:
  - 401: refresh token e retry
  - 403: mensagem de permissao/tenant
  - 404: sem dados do periodo
  - 409/422: erro de validacao de negocio
  - 5xx: indisponibilidade temporaria

## 7. Contratos de erro (padrao FastAPI)

Erros retornam geralmente:

{
  "detail": "mensagem"
}

Codigos mais comuns:
- 401 nao autenticado/token invalido
- 403 acesso negado (tenant/role)
- 404 recurso nao encontrado
- 409 conflito de negocio/idempotencia
- 422 validacao de payload/regra

## 8. Ordem recomendada de integracao Flutter

1) Auth (login, refresh, logout, me)
2) Summary (Home, Dashboard, KPIs, Alertas, Insights, Recomendacoes, Timeline)
3) Importacoes (upload csv)
4) Business cadastros (customer/product) se telas administrativas forem entrar na sprint
5) Endpoints internos apenas para operacao admin e diagnostico

## 9. Checklist rapido de pronto para app

- Cliente HTTP com interceptor Bearer + Correlation-ID
- Refresh token automatico em 401
- Parse de SummaryResponse completo
- Upload multipart para imports/csv
- Mapeamento de erros por status code
- Fallback de tela sem dados quando summary retornar 404
