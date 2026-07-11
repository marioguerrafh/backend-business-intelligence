# Eventos Publicados - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. Evento: kpi.recalculated

1. producer: KPI Orchestrator
2. topic: kpi.recalculated.v1
3. payload:
- company_id
- period_ref
- kpi_id
- formula_id
- value
- unit
- confidence_score
- orchestrator_run_id
- occurred_at

## 2. Evento: risk.detected

1. producer: Rule Orchestrator
2. topic: risk.detected.v1
3. payload:
- company_id
- period_ref
- kpi_id
- rule_id
- severity
- priority
- risk_code
- orchestrator_run_id
- occurred_at

## 3. Evento: recommendation.generated

1. producer: Recommendation Engine
2. topic: recommendation.generated.v1
3. payload:
- company_id
- period_ref
- recommendation_id
- linked_rule_id
- rank_score
- expected_impact
- orchestrator_run_id
- occurred_at

## 4. Evento: insight.generated

1. producer: Insight Engine
2. topic: insight.generated.v1
3. payload:
- company_id
- period_ref
- insight_id
- insight_type
- statement
- evidence_ref
- orchestrator_run_id
- occurred_at

## 5. Evento: executive.score.calculated

1. producer: Executive Score Engine
2. topic: executive.score.calculated.v1
3. payload:
- company_id
- period_ref
- financial_score
- commercial_score
- operational_score
- overall_score
- orchestrator_run_id
- occurred_at

## 6. Evento: summary.refreshed

1. producer: Summary Engine
2. topic: executive.summary.refreshed.v1
3. payload:
- company_id
- period_ref
- summary_version
- overall_score
- top_risks_count
- top_recommendations_count
- generated_at

## 7. Evento: timeline.snapshot.created

1. producer: Timeline Engine
2. topic: executive.timeline.snapshot.created.v1
3. payload:
- company_id
- snapshot_date
- overall_score
- top_kpis_ref
- top_alerts_ref
- top_insights_ref
- top_recommendations_ref
- occurred_at
