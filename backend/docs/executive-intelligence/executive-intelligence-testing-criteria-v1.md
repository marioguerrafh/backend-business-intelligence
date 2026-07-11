# Critérios de Teste - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. Unit tests

1. KPI Orchestrator
- resolução de dependências
- idempotência por run

2. Rule Orchestrator
- classificação de severidade e prioridade
- dedução de risk_code

3. Recommendation Engine
- ranking por impacto/confiança
- deduplicação por causa raiz

4. Insight Engine
- geração de statement a partir de evidências
- bloqueio de insight sem evidência

5. Executive Score Engine
- cálculo dos 4 scores
- validação de limites 0-100

6. Summary Engine
- composição correta do payload /v1/summary

7. Timeline Engine
- persistência de snapshot diário
- comparação entre janelas

## 2. Integration tests

1. pipeline ponta a ponta por tenant:
- ingest.completed -> summary.refreshed

2. consistência multi-tenant:
- dados de tenant A nunca vazam para tenant B

3. contrato de leitura:
- summary e timeline retornam schema esperado

## 3. Contract tests

1. eventos publicados v1:
- kpi.recalculated
- risk.detected
- recommendation.generated
- insight.generated
- executive.score.calculated
- summary.refreshed
- timeline.snapshot.created

2. REST:
- GET /v1/summary
- GET /v1/summary/timeline
- GET /v1/summary/risks
- GET /v1/summary/recommendations

## 4. Testes não funcionais

1. desempenho:
- P95 de /v1/summary <= 700 ms

2. robustez:
- reprocessamento após falha parcial sem duplicidade

3. observabilidade:
- logs com correlation_id em todos os estágios

4. segurança:
- enforcement de company_id em todos os acessos

## 5. Critérios de aprovação

1. 100% dos contratos críticos aprovados.
2. 0 regressões em isolamento multi-tenant.
3. Todos os scores dentro de faixa válida.
4. Nenhum insight órfão de evidência.
