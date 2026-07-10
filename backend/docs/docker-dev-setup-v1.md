# Docker Development Setup v1

Date: 2026-07-10
Scope: Backend FastAPI + PostgreSQL + Redis + PgAdmin

## 1. Objetivo

Permitir que qualquer desenvolvedor suba o backend completo com um unico comando:

```bash
docker compose up -d
```

Pre-requisito: Docker Desktop (ou Docker Engine) deve estar em execucao.

## 2. Servicos do compose

1. `api`: FastAPI com reload em desenvolvimento e health check HTTP.
2. `postgres`: banco principal com volume persistente e health check `pg_isready`.
3. `redis`: cache/broker com persistencia AOF e health check `PING`.
4. `pgadmin`: administracao visual do PostgreSQL com volume persistente e health check HTTP.
5. `migrate` (profile `tools`): executa `alembic upgrade head` manualmente quando desejado.

## 3. Arquivos criados

1. `docker-compose.yml`
2. `backend/Dockerfile` (multi-stage)
3. `backend/.dockerignore`
4. `backend/.env.docker`
5. `backend/alembic.ini`
6. `backend/alembic/env.py`
7. `backend/alembic/versions/20260710_0001_initial_schema.py`

## 4. Como subir localmente

1. No diretorio raiz do repositorio, execute:

```bash
docker compose up -d
```

2. Validar servicos:

```bash
docker compose ps
```

3. Acessos padrao:
- API: http://localhost:8000
- Health: http://localhost:8000/health
- PgAdmin: http://localhost:5050

## 5. Migracoes Alembic

A API ja executa `alembic upgrade head` antes de iniciar no ambiente de desenvolvimento via compose.

Comandos uteis:

1. Executar migracoes manualmente:

```bash
docker compose --profile tools run --rm migrate
```

2. Criar nova migration (quando houver mudanca de schema):

```bash
docker compose run --rm api alembic revision --autogenerate -m "descricao"
```

## 6. Variaveis de ambiente

1. Desenvolvimento em Docker usa `backend/.env.docker`.
2. Fora de Docker, pode usar `backend/.env` (com base em `backend/.env.example`).
3. Banco em Docker usa host `postgres`.

## 7. Redes e seguranca

1. Rede `bi_internal` (interna): postgres e redis isolados.
2. Rede `bi_public`: exposicao apenas do necessario (api e pgadmin).
3. Persistencia em volumes Docker para banco, redis e pgadmin.

## 8. Boas praticas adotadas

1. Dockerfile multi-stage para imagem menor e build mais previsivel.
2. Health checks para orquestracao confiavel.
3. Volumes persistentes para nao perder dados locais.
4. Separacao de variaveis por ambiente.
5. Alembic versionado para evolucao de schema sem quebrar contratos da API.

## 9. Troubleshooting rapido

1. Rebuild completo:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

2. Ver logs da API:

```bash
docker compose logs -f api
```

3. Ver status de health:

```bash
docker inspect --format='{{json .State.Health}}' bi_api
```
