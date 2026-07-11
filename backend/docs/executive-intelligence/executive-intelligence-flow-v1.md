# Fluxo Completo - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. Fluxo operacional (escrita)

1. Trigger de recalculo chega (ingestão ou scheduler).
2. KPI Orchestrator identifica KPIs impactados.
3. KPI Orchestrator resolve dependências e chama Formula Engine.
4. KPI Orchestrator persiste kpi_result e publica kpi.recalculated.
5. Rule Orchestrator consome kpi.recalculated e executa Rule DSL.
6. Rule Orchestrator persiste rule_evaluation e publica risk.detected.
7. Recommendation Engine consome risk.detected e aplica Recommendation DSL.
8. Recommendation Engine persiste recommendation_result e publica recommendation.generated.
9. Insight Engine consome eventos de KPI/risco/recomendação e produz insight_result.
10. Executive Score Engine recalcula scores e publica executive.score.calculated.
11. Summary Engine consolida visão executiva e publica summary.refreshed.
12. Timeline Engine cria snapshot diário para comparativos.

## 2. Fluxo de leitura (Flutter)

1. App chama GET /v1/summary.
2. Summary Engine lê executive_summary_view mais recente do tenant/período.
3. Summary retorna score geral, KPIs, alertas, insights, recomendações, tendências e próximos riscos.
4. App chama endpoint de timeline para comparações históricas.

## 3. Fluxo de governança semântica

1. Atualização de DSL (formula/rule/recommendation/ai_prompt).
2. Publicação de evento *.dsl.updated.
3. Orchestrators invalidam cache e recarregam catálogos.
4. Próxima execução já usa nova semântica sem recompilar sistema.

## 4. Garantias de consistência

1. Idempotência por orchestrator_run_id + company_id + period_ref.
2. Ordem parcial de execução por estágio.
3. Reprocessamento seguro em caso de falha parcial.
4. Auditoria por evento e por resultado persistido.
