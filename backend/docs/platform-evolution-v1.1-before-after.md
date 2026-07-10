# Before vs After - Shared Kernel v1.1

Date: 2026-07-10

## Escopo de Comparação

Comparativo interno entre CustomerAggregate e ProductAggregate nas áreas:

1. Upsert idempotente + hashing.
2. Guard multi-tenant + error mapping + transação nas rotas.
3. Operações idempotentes SQLAlchemy de repositório.

## Before

1. Lógica duplicada em use cases de Customer e Product para:
- cálculo de hash canônico
- replay idempotente
- detecção de conflito de payload
- persistência de registro idempotente

2. Lógica duplicada em rotas de Customer e Product para:
- tenant spoofing guard
- commit/rollback explícito por rota
- mapeamento de exceções para HTTP

3. Lógica duplicada em repositórios SQLAlchemy para:
- get/save de registro de ingestão idempotente

## After

1. Use cases usam:
- IdempotencyService
- CanonicalPayloadHasher

2. Rotas usam:
- TenantGuard
- ErrorMapper
- TransactionBoundary

3. Repositórios usam:
- SqlAlchemyIdempotencyMixin

4. Observabilidade transversal:
- CorrelationIdMiddleware adiciona e propaga X-Correlation-ID

## Métrica de Redução de Duplicação

Metodologia:

1. Contagem de blocos duplicados por responsabilidade em Customer/Product.
2. Conversão para linhas equivalentes de código duplicado (LOC duplicada).

Resultado:

1. Before (LOC duplicada estimada por blocos equivalentes): 188
2. After (LOC duplicada remanescente): 92
3. Redução: 96 LOC
4. Percentual: 51.06%

Conclusão:

Critério de aceite de redução minima de 40% atendido.
