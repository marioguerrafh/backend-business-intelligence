# RFC - Business Platform Evolution v1.1

Date: 2026-07-09
Author: Platform Guardian / Principal Software Architect
Status: Implemented (Sprint Shared Kernel v1.1)

## 1. Objetivo

Evoluir a plataforma com base no conjunto Auth Engine + CustomerAggregate + ProductAggregate, reduzindo duplicações, consolidando componentes compartilháveis e padronizando convenções para escalar o desenvolvimento dos próximos agregados sem regressão arquitetural.

Escopo desta RFC:

- Análise cruzada de padrões repetidos e violações DRY
- Definição de Shared Kernel v1.1
- Padrões de nomenclatura e estrutura únicos
- Plano de migração incremental sem quebra da arquitetura pública

Não escopo:

- Implementação de novos agregados
- Mudança de contratos públicos REST existentes

## 2. Diagnóstico Atual

### 2.1 Padrões repetidos e oportunidades de abstração

1. Upsert com idempotência + hash duplicado
- Customer: app/modules/business/application/use_cases.py
- Product: app/modules/business/application/product_use_cases.py
- Ambos repetem: lookup de idempotência, cálculo de hash, replay, conflito e logging.

2. Roteamento REST de upsert/get duplicado
- Customer: app/modules/business/interfaces/api/routes.py
- Product: app/modules/business/interfaces/api/product_routes.py
- Ambos repetem: tenant guard, construção de command, commit/rollback, mapeamento de exceções, correlation id.

3. Event publisher in-memory duplicado
- Customer: app/modules/business/infrastructure/event_publisher.py
- Product: app/modules/business/infrastructure/product_event_publisher.py
- Estrutura e comportamento são equivalentes, mudando apenas tipo de evento e topic.

4. Container/wiring duplicado
- Customer: app/modules/business/infrastructure/container.py
- Product: app/modules/business/infrastructure/product_container.py
- Mesmo padrão de logger + repository + publisher + use cases.

5. Repository patterns repetidos
- Customer: app/modules/business/infrastructure/repositories.py
- Product: app/modules/business/infrastructure/product_repositories.py
- Mesmos mecanismos de save/get by external ref/idempotency.

### 2.2 Inconsistências de nomenclatura/organização

1. Business module mistura arquivos genéricos e prefixados
- Customer usa: contracts.py, use_cases.py, repositories.py, event_publisher.py, container.py
- Product usa: product_contracts.py, product_use_cases.py, product_repositories.py, product_event_publisher.py, product_container.py
- Resultado: baixa previsibilidade para onboarding.

2. Auth diverge do padrão de Business
- Auth usa application/schemas.py para commands.
- Business usa application/contracts.py e application/product_contracts.py.
- Convergência recomendada para uma convenção única de command/query contracts.

3. Modelo de persistência concentrado
- app/modules/business/infrastructure/models.py concentra múltiplos agregados e cresce rapidamente.
- Escalabilidade de manutenção reduzida com aumento de agregados.

### 2.3 DRY / SOLID / responsabilidade

1. Violação DRY significativa na pipeline de upsert idempotente.
2. Violação DRY na camada de interface (error mapping + transaction boundary + tenant guard).
3. Princípio Open/Closed comprometido: adicionar novo agregado exige copiar e colar blocos extensos.

### 2.4 Observabilidade, transação e consistência

1. Estratégia de transação inconsistente
- Auth: commit/rollback no dependency provider (auth/interfaces/api/dependencies.py)
- Business: commit/rollback em cada rota (business/interfaces/api/*.py)

2. Event publishing ainda in-memory
- Bom para v1.0, insuficiente para confiabilidade cross-module em produção (ausência de outbox transacional).

### 2.5 Segurança e multi-tenant

1. Tenant guard implementado em Customer/Product, mas repetido por rota.
2. Ausência de componente único de política de tenant para comandos de domínio.

## 3. Arquitetura-Alvo v1.1

## 3.1 Shared Kernel v1.1 (novos componentes comuns)

1. shared/application/idempotency.py
- Contrato e serviço base para:
  - resolve replay
  - conflito de payload
  - canonical payload hash
- Interface genérica para aggregate_id.

2. shared/application/upsert.py
- Template de UpsertUseCaseBase com hooks:
  - find_existing(command)
  - validate_uniqueness(command, target)
  - create_new(command)
  - update_existing(target, command)
  - build_event(entity, command)

3. shared/interfaces/api/tenant.py
- TenantGuard dependency unificada:
  - assert_payload_company(principal, payload.company_id)
  - assert_path_company(principal, company_id)

4. shared/interfaces/api/errors.py
- Mapper comum de exceções de domínio/infra para HTTP status.
- Inclui mapeamento padrão de IntegrityError -> 409.

5. shared/interfaces/api/transaction.py
- Unidade transacional única por request para módulos de negócio.
- Remove commit/rollback duplicado de rotas.

6. shared/infrastructure/messaging/outbox.py
- Contrato e adapter base para publicação confiável de eventos de integração.
- Evolução natural do publisher in-memory para durável.

7. shared/infrastructure/repository_mixins.py
- Mixins comuns para operações idempotentes e external refs.

## 3.2 Convenção de estrutura por agregado (padrão único)

Adotar padrão por agregado dentro de business:

- app/modules/business/customer/domain/...
- app/modules/business/customer/application/...
- app/modules/business/customer/infrastructure/...
- app/modules/business/customer/interfaces/api/...
- app/modules/business/product/domain/...
- app/modules/business/product/application/...
- ...

Benefícios:

- Remove colisão entre arquivos genéricos e prefixados
- Facilita ownership por agregado
- Mantém bounded context com fronteiras explícitas

## 3.3 Convenção de nomenclatura v1.1

1. Command/query:
- Sempre em contracts.py por agregado.
- Nunca schemas.py para command de domínio (schemas reservados para HTTP DTO).

2. Use cases:
- Sempre use_cases.py por agregado.

3. Ports:
- repository.py
- event_publisher.py
- (opcional) policies.py, services.py

4. Infra:
- models.py (somente do agregado)
- repositories.py
- container.py

5. Interface:
- schemas.py
- routes.py
- dependencies.py (quando necessário)

## 3.4 Política de transação e consistência

1. Transação por request centralizada em dependency shared.
2. Use cases não fazem commit explícito.
3. Publisher de domínio escreve em outbox dentro da mesma transação.
4. Dispatcher assíncrono publica integração fora do request path.

## 3.5 Política de segurança

1. Tenant guard obrigatório em todas rotas de agregado.
2. Política de role opcional por operação com decorator/dependency comum.
3. company_id sempre derivado/validado contra principal.

## 4. Plano de Migração v1.1

### Fase A - Fundamentos Shared Kernel

1. Introduzir módulos shared de tenant guard, error mapper e transaction boundary.
2. Introduzir serviço idempotency base e utilitário de payload hashing canônico.
3. Manter endpoints e contratos públicos sem alteração.

### Fase B - Refatoração interna incremental

1. Refatorar CustomerAggregate para consumir componentes shared.
2. Refatorar ProductAggregate para consumir os mesmos componentes.
3. Eliminar duplicação de lógica de upsert/idempotência/erro/transação.

### Fase C - Organização por agregado

1. Reorganizar business para pastas por agregado.
2. Atualizar imports internos gradualmente.
3. Garantir compatibilidade durante transição via adaptadores temporários.

### Fase D - Confiabilidade de eventos

1. Introduzir outbox para Customer/Product.
2. Migrar publisher in-memory para publisher durável.
3. Adicionar contract tests de eventos N/N-1.

## 5. Critérios de Aceite v1.1

1. Nenhuma mudança de contrato REST público existente.
2. Redução mensurável de duplicação:
- >=40% de redução de linhas duplicadas entre Customer/Product use cases e routes.

3. Estratégia transacional única para Auth + Business.
4. Tenant guard unificado aplicado em 100% dos endpoints de escrita/leitura multi-tenant.
5. Outbox habilitado para pelo menos Customer e Product (ou feature-flag com fallback explícito).
6. Suite de testes verde com cenários de:
- tenant spoofing
- IntegrityError mapping
- idempotent replay/conflict
- dispatch de evento via outbox (quando ativo)

## 6. Riscos e Mitigações

1. Risco: refatoração extensa causar regressão.
- Mitigação: migração por fases com testes de regressão completos a cada etapa.

2. Risco: reorganização de pastas quebrar imports.
- Mitigação: camada de compatibilidade temporária e PRs menores.

3. Risco: aumento de complexidade inicial do shared kernel.
- Mitigação: começar por 3 componentes de maior impacto (tenant, errors, transaction) antes de abstrações avançadas.

## 7. Conclusão

A plataforma já possui base sólida com Auth, Customer e Product, porém com duplicações estruturais significativas. A evolução v1.1 proposta transforma o padrão atual em um framework interno de agregados, preservando DDD/Clean, aumentando velocidade de entrega e reduzindo risco operacional.

Recomendação final: aprovar RFC v1.1 e iniciar Fase A imediatamente.

## 8. Status de Implementação (Sprint Shared Kernel)

Implementado nesta sprint (sem quebra de contrato REST):

1. Shared application:
- IdempotencyService: app/shared/application/idempotency/service.py
- CanonicalPayloadHasher: app/shared/application/hashing/canonical_payload_hasher.py
- TransactionManager: app/shared/application/transaction/manager.py
- ValidationResult: app/shared/application/validation/validation_result.py

2. Shared domain:
- DomainEvent base: app/shared/domain/events/domain_event.py
- Primitives: app/shared/domain/primitives/{identifiers.py,timestamp.py,correlation_id.py}

3. Shared infrastructure:
- StructuredLogger: app/shared/infrastructure/logging/structured_logger.py
- Outbox interface: app/shared/infrastructure/messaging/outbox.py
- EventDispatcher interface: app/shared/infrastructure/messaging/event_dispatcher.py
- Repository mixin de idempotência SQLAlchemy: app/shared/infrastructure/repository/mixins.py

4. Shared interfaces API:
- TenantGuard: app/shared/interfaces/api/tenant_guard.py
- ErrorMapper: app/shared/interfaces/api/error_mapper.py
- TransactionBoundary: app/shared/interfaces/api/transaction_boundary.py
- CorrelationIdMiddleware: app/shared/interfaces/api/correlation_id_middleware.py

5. Refatoração Customer/Product para consumir Shared Kernel:
- Use cases migrados para IdempotencyService + CanonicalPayloadHasher
- Rotas migradas para TenantGuard + ErrorMapper + TransactionBoundary
- Repositórios migrados para SqlAlchemyIdempotencyMixin
- CorrelationIdMiddleware registrado em app/main.py

6. Validação:
- Testes automatizados: 36 -> 46 passando (suite verde)
