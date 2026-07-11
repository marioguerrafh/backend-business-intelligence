# Diagrama de Arquitetura - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

```mermaid
flowchart LR
    A[Ingestion Completed Event] --> B[KPI Orchestrator]
    B --> C[Formula Engine]
    C --> D[(kpi_result)]
    B --> E[kpi.recalculated.v1]

    E --> F[Rule Orchestrator]
    F --> G[(rule_evaluation)]
    F --> H[risk.detected.v1]

    H --> I[Recommendation Engine]
    I --> J[(recommendation_result)]
    I --> K[recommendation.generated.v1]

    E --> L[Insight Engine]
    H --> L
    K --> L
    L --> M[(insight_result)]
    L --> N[insight.generated.v1]

    E --> O[Executive Score Engine]
    O --> P[(executive_score)]
    O --> Q[executive.score.calculated.v1]

    Q --> R[Summary Engine]
    N --> R
    K --> R
    H --> R
    R --> S[(executive_summary_view)]
    R --> T[summary.refreshed.v1]

    T --> U[Timeline Engine]
    U --> V[(timeline_snapshot)]

    W[Flutter App] --> X[Executive Dashboard API]
    X --> R
    X --> U

    Y[Formula DSL] --> C
    Z[Rule DSL] --> F
    AA[Recommendation DSL] --> I
    AB[AI Prompt DSL] --> L
```

## Observações

1. Todos os módulos operam com isolamento por company_id.
2. Todos os cálculos e decisões são auditáveis por orchestrator_run_id.
3. Todos os motores usam apenas modelo canônico e DSLs oficiais.
