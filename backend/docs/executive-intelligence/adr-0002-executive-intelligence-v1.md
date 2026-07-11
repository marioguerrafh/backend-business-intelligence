# ADR-0002 - Arquitetura da Executive Intelligence Platform v1.0

Date: 2026-07-10
Status: Accepted

## Contexto

A plataforma já possui motores fundamentais (Auth, Formula, Rule DSL, Recommendation DSL, modelo canônico e dicionário semântico). O objetivo agora é transformar resultados analíticos em decisões executivas de forma consistente para o aplicativo.

## Decisões

1. Adotar orquestração em dois estágios:
- Stage A: KPI Orchestrator.
- Stage B: Rule/Recommendation/Insight/Score/Timeline.

2. Summary Engine como agregador de leitura:
- Endpoint principal para Flutter: GET /v1/summary.

3. Scores em quatro eixos + score geral:
- Financeiro, Comercial, Operacional, Geral, todos de 0 a 100.

4. Timeline diária como fonte comparativa oficial:
- Hoje, ontem, último mês, último ano.

5. Uso exclusivo de DSLs oficiais:
- Fórmulas, regras, recomendações e prompts de IA.

6. Contratos de API versionados e estáveis:
- Sem quebra de contrato para o aplicativo.

## Consequências Positivas

1. Camada executiva desacoplada de ERP.
2. Evolução rápida de regra e recomendação sem deploy.
3. Melhor explicabilidade para gestão.
4. Menor tempo para decisão baseada em evidência.

## Consequências Negativas

1. Aumento de complexidade de governança semântica.
2. Necessidade de controle rigoroso de versões dos DSLs.

## Alternativas Consideradas

1. Construir resumo direto em uma única query síncrona.
- Rejeitada por acoplamento e baixa escalabilidade.

2. Embutir recomendação no Rule Engine.
- Rejeitada para manter responsabilidade única e evolução independente.

## Conformidade

1. Mantém DDD/Clean Architecture/SOLID.
2. Não altera arquitetura de módulos já existentes.
3. Mantém contratos existentes e cria novos contratos executivos versionados.
