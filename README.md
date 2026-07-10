# Business Intelligence Platform

Plataforma SaaS multi-tenant de Business Intelligence para gestao operacional e executiva.

## Estado atual

O projeto ja possui base backend funcional com:

1. Arquitetura em camadas (Clean Architecture + SOLID).
2. Multi-tenant por `company_id`.
3. Auth Engine com autenticacao e autorizacao.
4. Agregados de negocio iniciais: Customer e Product.
5. Shared Kernel v1.1 aplicado para reduzir duplicacao e padronizar componentes transversais.
6. Catalogos oficiais e RFCs para KPI Engine e Rule Engine.

## Estrutura principal

1. `backend/`: API FastAPI, modulos de dominio, infraestrutura e testes.
2. `.ai/`: guias de direcionamento para evolucao da plataforma com IA.
3. `.github/copilot-instructions.md`: principios arquiteturais e de engenharia.

## Quickstart local (Docker)

No diretorio raiz do repositorio:

```bash
docker compose up -d
```

Esse comando sobe API, PostgreSQL, Redis e PgAdmin para desenvolvimento.

## Documentacao chave

1. `backend/docs/status-servidor-visao-plataforma-v1.md`: status atual e visao de como ficara pronto.
2. `backend/docs/rfc-platform-evolution-v1.1.md`: evolucao arquitetural e shared kernel.
3. `backend/docs/kpi-catalogo-oficial-v1.md`: catalogo oficial de KPIs por dominio.
4. `backend/docs/rfc-kpi-engine-v1.md`: definicao do KPI Engine.
5. `backend/docs/business-rules-catalog-v1.md`: catalogo oficial de regras de negocio.
6. `backend/docs/rfc-rule-engine-v1.md`: definicao do Rule Engine.
7. `backend/docs/docker-dev-setup-v1.md`: setup completo com Docker e Alembic.

## Proximo foco

1. Implementar fluxo operacional do KPI Engine com dados reais.
2. Ativar regras prioritarias P0 e P1 do Rule Engine.
3. Consolidar camada executiva com alertas, recomendacoes e explicacao por IA.

## Como contribuir com IA (fluxo sugerido)

1. Abra o Copilot Chat.
2. Peça para ler `.ai/project.md`.
3. Peça para ler o documento alvo em `backend/docs/` (RFC/catalogo).
4. Solicite implementacao incremental com testes e sem quebrar contratos publicos.
