# Contratos REST - Executive Dashboard API v1.0

Date: 2026-07-10
Status: Proposed

## 1. GET /v1/summary

### Query params

1. company_id (required)
2. period_ref (optional, default: current)
3. period_grain (optional: day|week|month)

### Response 200

1. summary_id
2. company_id
3. period_ref
4. generated_at
5. scores
- overall
- financial
- commercial
- operational
6. kpis
- kpi_id
- name
- value
- unit
- trend
- health
7. alerts
- alert_id
- severity
- priority
- title
- description
8. insights
- insight_id
- type
- statement
- evidence
9. recommendations
- recommendation_id
- title
- rank
- expected_impact
- owner_role
- sla_target
10. trends
- period_comparison
- top_movements
11. next_risks
- risk_code
- probability
- potential_impact

### Error codes

1. 400 invalid period_ref
2. 401 unauthorized
3. 403 forbidden_tenant_scope
4. 404 summary_not_found
5. 422 semantic_validation_error

## 2. GET /v1/summary/timeline

### Query params

1. company_id (required)
2. reference_date (optional)
3. window (optional: 30d|90d|365d)

### Response 200

1. company_id
2. window
3. points
- snapshot_date
- overall_score
- financial_score
- commercial_score
- operational_score
4. comparisons
- today_vs_yesterday
- today_vs_last_month
- today_vs_last_year

## 3. GET /v1/summary/risks

### Query params

1. company_id (required)
2. period_ref (optional)
3. severity (optional)

### Response 200

1. company_id
2. risks
- risk_code
- severity
- priority
- source_kpi
- triggered_rule
- first_seen_at
- recommended_actions

## 4. GET /v1/summary/recommendations

### Query params

1. company_id (required)
2. period_ref (optional)
3. priority (optional)

### Response 200

1. company_id
2. recommendations
- recommendation_id
- rank_score
- expected_impact
- confidence
- owner_role
- sla_target
- playbook_steps

## 5. Compatibilidade de versão

1. Prefixo de versão mantido em /v1.
2. Campos novos apenas aditivos.
3. Campos existentes não serão renomeados sem RFC/ADR de breaking change.
