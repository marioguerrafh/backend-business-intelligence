# ADR-0001 - Shared Kernel v1.1 para Customer/Product

Date: 2026-07-10
Status: Accepted

## Contexto

Os agregados Customer e Product possuíam duplicação relevante em quatro áreas:

1. Pipeline de idempotência e hashing no upsert.
2. Guardas multi-tenant e mapeamento de erro HTTP nas rotas.
3. Fronteira transacional por endpoint.
4. Operações SQLAlchemy de ingestão/idempotência nos repositórios.

A diretriz da sprint v1.1 exige consolidar esses pontos no Shared Kernel sem alterar contratos REST públicos.

## Decisão

Adotar Shared Kernel com componentes reutilizáveis e integrar Customer/Product:

1. Application:
- IdempotencyService
- CanonicalPayloadHasher
- TransactionManager
- ValidationResult

2. Domain:
- DomainEvent (base)
- Primitive value objects de identificação/tempo/correlação

3. Infrastructure:
- StructuredLogger
- Outbox e EventDispatcher como interfaces (preparo para evolução confiável)
- SqlAlchemyIdempotencyMixin

4. Interfaces API:
- TenantGuard
- ErrorMapper
- TransactionBoundary
- CorrelationIdMiddleware

## Consequências

Positivas:

1. Redução de duplicação entre Customer/Product.
2. Menor acoplamento entre regras de domínio e camada web.
3. Padronização da semântica transacional e tratamento de erro nas rotas de negócio.
4. Preparação explícita para outbox sem introduzir mudança de comportamento nesta sprint.

Negativas:

1. Aumento inicial de artefatos compartilhados para manter.
2. Necessidade de disciplina para evitar que Shared Kernel vire camada genérica excessiva.

## Alternativas Consideradas

1. Manter código duplicado e postergar abstração.
- Rejeitada por custo crescente de manutenção e inconsistência de comportamento.

2. Introduzir base classes abstratas complexas para todos os use cases.
- Rejeitada nesta sprint para reduzir risco de regressão e manter mudança incremental.

## Conformidade

1. Nenhum endpoint público alterado.
2. Nenhum novo agregado criado.
3. Nenhuma nova funcionalidade de negócio adicionada.
4. DDD/Clean/SOLID preservados por separação de responsabilidades.
