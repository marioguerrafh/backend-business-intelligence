# Backend FastAPI

Backend da plataforma SaaS multi-tenant de Business Intelligence.

## Objetivo

Entregar uma base robusta para operacao transacional e inteligencia de negocio, com seguranca, rastreabilidade e evolucao incremental orientada por RFCs.

## Stack

1. Python 3.12
2. FastAPI
3. SQLAlchemy
4. PostgreSQL (prod) / SQLite (testes)
5. Pytest

## Arquitetura

1. Clean Architecture com separacao em dominio, aplicacao, infraestrutura e interfaces.
2. Multi-tenant obrigatorio com `company_id`.
3. Shared Kernel para componentes transversais.
4. Evolucao por modulos de negocio (modular monolith).

## Modulos entregues

1. Auth Engine
- login/refresh/logout
- autorizacao por papeis
- validacoes de token e principal

2. Business CustomerAggregate
- upsert/get
- idempotencia
- hardening de tenant e conflito

3. Business ProductAggregate
- upsert/get
- idempotencia
- hardening alinhado ao padrao do Customer

4. Shared Kernel v1.1
- transaction boundary
- tenant guard
- error mapper
- canonical payload hasher
- idempotency service
- correlation id middleware

## Rodar localmente

1. Crie e ative ambiente virtual.
2. Instale dependencias:

```bash
pip install -e .[dev]
```

3. Rode a API:

```bash
uvicorn app.main:app --reload
```

4. Execute testes:

```bash
pytest -q
```

## Rodar com Docker (um comando)

No diretorio raiz do repositorio:

```bash
docker compose up -d
```

Servicos disponiveis:

1. API FastAPI: `http://localhost:8000`
2. Healthcheck: `http://localhost:8000/health`
3. PostgreSQL: `localhost:5432`
4. Redis: `localhost:6379`
5. PgAdmin: `http://localhost:5050`

Migracoes Alembic:

1. Aplicar migracoes:

```bash
docker compose --profile tools run --rm migrate
```

2. Criar migration nova:

```bash
docker compose run --rm api alembic revision --autogenerate -m "descricao"
```

## Qualidade atual

1. Suite de testes automatizados verde.
2. Contratos REST existentes preservados.
3. Base preparada para evolucao de KPI Engine e Rule Engine.

## Documentacao de referencia

1. `docs/status-servidor-visao-plataforma-v1.md`
2. `docs/rfc-platform-evolution-v1.1.md`
3. `docs/kpi-catalogo-oficial-v1.md`
4. `docs/rfc-kpi-engine-v1.md`
5. `docs/business-rules-catalog-v1.md`
6. `docs/rfc-rule-engine-v1.md`
7. `docs/docker-dev-setup-v1.md`

## Proximos passos

1. Implementar KPI Engine conforme RFC.
2. Implementar Rule Engine conforme RFC e catalogo de regras.
3. Publicar camada executiva com explicacoes de IA orientadas a decisao.
