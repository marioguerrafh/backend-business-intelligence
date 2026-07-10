# RFC-ProductAggregate-v1

Date: 2026-07-09
Author: Principal DDD Architect
Status: Approved for implementation

## Context

This RFC defines ProductAggregate as the second canonical aggregate in Business Engine, using CustomerAggregate (Golden Aggregate v1.0) as the mandatory implementation blueprint.

## Scope

Implement only ProductAggregate with:

- Domain entity and invariants
- Value objects
- Repository port
- SQLAlchemy adapter
- Use cases (UpsertProduct, GetProduct)
- Domain event (BusinessProductUpserted)
- API contracts and routes
- P0/P1 hardening parity with CustomerAggregate
- Unit/integration tests
- Production readiness and gate review artifacts

## Architectural constraints

- Keep Clean Architecture layers unchanged.
- Preserve DDD boundaries.
- Preserve existing public architecture style and conventions.
- Any divergence from CustomerAggregate must be exclusively business-rule driven.

## Product domain model

Canonical fields:

- product_id
- company_id
- sku
- name
- category (optional)
- unit_of_measure
- status
- default_cost
- default_price
- tax_profile_ref (optional)
- external_refs
- created_at, updated_at

## Business invariants (Product-specific)

1. company_id is mandatory.
2. sku is mandatory and tenant-unique.
3. name is mandatory.
4. unit_of_measure is mandatory.
5. default_cost and default_price are non-negative.
6. external reference tuple items must be valid and normalized.

## Why these differences from CustomerAggregate

Differences are restricted to Product business semantics:

- Product uses SKU uniqueness instead of customer document uniqueness.
- Product uses pricing validation (non-negative cost/price).
- Product does not require contact channels, unlike active customer rule.

No other architectural differences are allowed.

## Use cases

### UpsertProduct

- Resolve by external reference
- Fallback resolve by `(company_id, sku)`
- Prevent duplicate SKU in tenant
- Enforce idempotency by `(company_id, source_system, source_record_id)` + payload hash
- Publish BusinessProductUpserted only on non-replay execution

### GetProduct

- Resolve by `(company_id, product_id)`
- Raise not-found on missing entity

## Event contract

BusinessProductUpserted payload:

- event_id
- occurred_at
- company_id
- product_id
- source_system
- source_record_id
- canonical_schema_version

Integration event topic:

- business.product.upserted

## Security and multi-tenant hardening parity (P0)

- Tenant spoofing blocked in API routes.
- company_id from payload/path must match authenticated principal tenant.

## Concurrency hardening parity (P0)

- SQL uniqueness constraints remain final guard.
- IntegrityError mapped to HTTP 409 conflict.

## Idempotency and request-path hardening parity (P1)

- Product ingestion idempotency record table.
- Replays with same payload are accepted with no event duplication.
- Replays with divergent payload raise idempotency conflict.
- No runtime create_all in request path.

## Testing criteria

- Unit: domain invariants and use-case behavior
- Integration: SQL repository roundtrip and idempotency
- API hardening: tenant spoofing, IntegrityError mapping, create_all absent from request path
- Full regression suite must pass

## Production readiness criteria

- DDD boundaries: pass
- Clean architecture layering: pass
- Tenant isolation at API boundary: pass
- SQL constraints and conflict mapping: pass
- Idempotency: pass
- Observability baseline (structured logs + correlation id): pass
- Test evidence for all P0/P1 scenarios: pass

## Gate review output

A dedicated gate review document must be produced after implementation with verdict and evidence.
