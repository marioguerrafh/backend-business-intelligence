# Integration Hub

## Objetivo

O modulo integrations centraliza conectividade ERP com arquitetura baseada em providers.

## Arquitetura

- Domain: entidades de conexao e job.
- Application: contratos, interface ERPProvider, provider registry e service.
- Infrastructure: modelos SQLAlchemy, repositorio, seguranca de credenciais e container.
- Providers: Omie provider completo + providers preparados para expansao.
- Interfaces API: endpoints em /v1/integrations.

## Fluxo

1. Cliente conecta ERP por POST /v1/integrations/connect.
2. Credenciais sao criptografadas e persistidas.
3. POST /v1/integrations/{id}/sync ou /full-sync cria integration_sync_job.
4. Provider executa sync e mapeia payload ERP para canonical.
5. Gateway persiste em imported_* e publica ingest.completed.v1.
6. Pipeline Coordinator existente e invocado, sem duplicar orquestracao.
7. Eventos integration.sync.started/completed/failed sao persistidos.

## Seguranca

- Credenciais armazenadas criptografadas (Fernet).
- Credenciais nunca retornam pela API.
- Logs usam mascaramento de campos sensiveis.

## Idempotencia

- Persistencia canonical reutiliza regras de deduplicacao por source_record_id + source_system + company_id.
- Repeticao de sync incremental nao duplica fatos ja importados.

## Providers suportados

- omie
- conta_azul
- tiny
- bling
- sap
- totvs
- senior
- sankhya
- oracle
- dynamics
