# RFC - Executive Intelligence Platform v1.0

Date: 2026-07-10
Author: Principal Software Architect + Chief Business Intelligence Officer + Principal Backend Engineer + Product Owner
Status: Proposed

## 1. Objetivo

Definir a arquitetura completa da camada executiva da plataforma para transformar KPIs em decisões, com foco em valor ao usuário final e não em infraestrutura.

## 2. Escopo

Inclui os módulos:

1. KPI Orchestrator
2. Rule Orchestrator
3. Recommendation Engine
4. Insight Engine
5. Executive Score Engine
6. Summary Engine
7. Timeline Engine
8. Executive Dashboard API

Não inclui:

1. Alterações de contratos já públicos fora da camada executiva.
2. Alterações estruturais no Auth Engine, Shared Kernel e Business Engine.
3. Acoplamento a ERP específico.

## 3. Princípios Arquiteturais

1. ERP-agnóstico: apenas Canonical Data Model e DSLs oficiais.
2. Runtime-configurable: regras e recomendações sem alteração de código.
3. Auditabilidade total: trilha de cálculo, decisão e publicação.
4. Multi-tenant rigoroso por company_id.
5. Explicabilidade executiva: cada decisão deve ser justificável.
6. Determinismo com idempotência por company_id + period_ref + orchestrator_run_id.

## 4. Módulos e Responsabilidades

### 4.1 KPI Orchestrator

1. Descobrir KPIs com recálculo necessário.
2. Resolver dependências de fórmulas.
3. Acionar Formula Engine.
4. Persistir resultados canônicos e auditoria.

### 4.2 Rule Orchestrator

1. Executar Rule Engine com Rule DSL.
2. Classificar severidade e prioridade.
3. Detectar riscos ativos e emergentes.

### 4.3 Recommendation Engine

1. Selecionar recomendações ativas por contexto.
2. Priorizar por impacto esperado e confiança.
3. Deduplicar recomendações por risco/causa.

### 4.4 Insight Engine

1. Gerar insights executivos em linguagem de negócio.
2. Relacionar causa -> efeito com evidências dos KPIs.
3. Publicar frases orientadas a ação.

### 4.5 Executive Score Engine

1. Calcular Saúde Financeira (0-100).
2. Calcular Saúde Comercial (0-100).
3. Calcular Saúde Operacional (0-100).
4. Calcular Saúde Geral (0-100).

### 4.6 Summary Engine

1. Compor payload executivo para Flutter em GET /v1/summary.
2. Agregar score, KPIs, alertas, insights, recomendações, tendências e próximos riscos.

### 4.7 Timeline Engine

1. Persistir snapshots diários.
2. Comparar hoje, ontem, último mês, último ano.
3. Disponibilizar série temporal para dashboard e IA.

### 4.8 Executive Dashboard API

1. Expor contratos REST estáveis para o aplicativo.
2. Garantir paginação, filtros por período e consistência de schema.

## 5. Dependências com motores existentes

1. Formula Engine v1.0
2. Formula DSL v1.0
3. Rule DSL v1.0
4. Recommendation DSL v1.0
5. AI Prompt DSL v1.0
6. Canonical Data Model v1.0
7. Business Semantic Dictionary v1.0

## 6. Fluxo Macro

1. Trigger de recálculo entra no KPI Orchestrator.
2. KPI Orchestrator calcula e persiste resultados.
3. Rule Orchestrator executa regras e riscos.
4. Recommendation Engine prioriza ações.
5. Insight Engine gera narrativa executiva.
6. Executive Score Engine calcula os 4 scores.
7. Timeline Engine salva snapshot diário.
8. Summary Engine compõe resposta do endpoint executivo.

## 7. NFRs (Não Funcionais)

1. P95 do GET /v1/summary <= 700 ms (cache warm).
2. P95 do pipeline completo <= 5 min por tenant por ciclo diário.
3. RPO: 24h para camada executiva.
4. RTO: 2h para restauração de leitura executiva.
5. Observabilidade com métricas, logs estruturados e correlação.

## 8. Segurança

1. Isolamento por company_id em leitura e escrita.
2. Claims do Auth Engine obrigatórios na borda da API.
3. Nenhum insight/recomendação pode usar dados fora do tenant.

## 9. Estratégia de rollout

1. Fase 1: Summary v1 com FIN/COM/EST.
2. Fase 2: inclusão PROD/RH/ATD.
3. Fase 3: score geral com risco preditivo.

## 10. Critérios de aceite da camada executiva

1. Pipeline completo executando ponta a ponta.
2. Endpoint GET /v1/summary retornando contrato completo.
3. Comparativos temporais funcionais (hoje, ontem, mês, ano).
4. Todos os resultados auditáveis por run.
5. Regras e recomendações alteráveis sem recompilar serviços.
