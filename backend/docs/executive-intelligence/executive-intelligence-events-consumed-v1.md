# Eventos Consumidos - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. KPI Orchestrator consome

1. ingest.completed.v1
- origem: imports/erp pipeline
- uso: descobrir quais KPIs recalcular por entidade alterada

2. formula.dsl.updated.v1
- origem: governance semântica
- uso: invalidar cache de plano de cálculo

## 2. Rule Orchestrator consome

1. kpi.recalculated.v1
- origem: KPI Orchestrator
- uso: avaliar regras por KPI recalculado

2. rule.dsl.updated.v1
- origem: governance semântica
- uso: recarregar catálogo de regras

## 3. Recommendation Engine consome

1. risk.detected.v1
- origem: Rule Orchestrator
- uso: selecionar recomendações por risco

2. recommendation.dsl.updated.v1
- origem: governance semântica
- uso: atualizar catálogo sem redeploy

## 4. Insight Engine consome

1. kpi.recalculated.v1
- origem: KPI Orchestrator
- uso: detectar variações relevantes

2. risk.detected.v1
- origem: Rule Orchestrator
- uso: compor narrativa de risco

3. recommendation.generated.v1
- origem: Recommendation Engine
- uso: fechar insight com próximo passo

## 5. Executive Score Engine consome

1. kpi.recalculated.v1
- origem: KPI Orchestrator
- uso: recalcular scores por domínio

## 6. Summary Engine consome

1. executive.score.calculated.v1
2. insight.generated.v1
3. recommendation.generated.v1
4. risk.detected.v1
- uso: atualizar aggregate de leitura do endpoint

## 7. Timeline Engine consome

1. executive.summary.refreshed.v1
- uso: persistir snapshot diário para comparativos históricos
