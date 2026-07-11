# Modelo de Dados - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. Entidades de escrita

### 1.1 kpi_result

1. kpi_result_id (pk)
2. company_id (idx)
3. period_ref (idx)
4. period_grain (day|week|month)
5. kpi_id (idx)
6. formula_id
7. value
8. unit
9. confidence_score
10. calculated_at
11. orchestrator_run_id (idx)

### 1.2 rule_evaluation

1. rule_evaluation_id (pk)
2. company_id (idx)
3. period_ref (idx)
4. kpi_id (idx)
5. rule_id (idx)
6. status_health (green|yellow|red)
7. severity (low|medium|high|critical)
8. priority (p0|p1|p2|p3)
9. risk_code
10. fired_at
11. orchestrator_run_id (idx)

### 1.3 recommendation_result

1. recommendation_result_id (pk)
2. company_id (idx)
3. period_ref (idx)
4. recommendation_id (idx)
5. linked_rule_id
6. rank_score
7. expected_impact_value
8. expected_impact_unit
9. confidence_score
10. dedupe_group_key
11. generated_at

### 1.4 insight_result

1. insight_result_id (pk)
2. company_id (idx)
3. period_ref (idx)
4. insight_type (trend|risk|opportunity|anomaly)
5. title
6. statement
7. evidence_json
8. generated_at

### 1.5 executive_score

1. executive_score_id (pk)
2. company_id (idx)
3. period_ref (idx)
4. financial_score (0-100)
5. commercial_score (0-100)
6. operational_score (0-100)
7. overall_score (0-100)
8. score_version
9. calculated_at

### 1.6 timeline_snapshot

1. timeline_snapshot_id (pk)
2. company_id (idx)
3. snapshot_date (idx)
4. overall_score
5. top_kpis_json
6. top_alerts_json
7. top_insights_json
8. top_recommendations_json
9. top_risks_json
10. created_at

### 1.7 orchestrator_run

1. orchestrator_run_id (pk)
2. company_id (idx)
3. pipeline_stage (kpi|rule|recommendation|insight|score|timeline|summary)
4. started_at
5. finished_at
6. status (success|partial|failed)
7. error_summary
8. correlation_id

## 2. Entidades de leitura (view model)

### 2.1 executive_summary_view

1. company_id
2. period_ref
3. overall_score
4. financial_score
5. commercial_score
6. operational_score
7. kpis_json
8. alerts_json
9. insights_json
10. recommendations_json
11. trends_json
12. next_risks_json
13. generated_at

## 3. Regras de modelagem

1. Todas as tabelas possuem company_id.
2. Todas as tabelas executivas possuem period_ref.
3. Toda persistência executiva referencia orchestrator_run_id quando aplicável.
4. Índices obrigatórios: company_id + period_ref para leitura rápida.

## 4. Política de retenção

1. kpi_result: 36 meses
2. rule_evaluation: 24 meses
3. recommendation_result: 24 meses
4. insight_result: 24 meses
5. executive_score: 36 meses
6. timeline_snapshot: 60 meses
7. orchestrator_run: 12 meses
