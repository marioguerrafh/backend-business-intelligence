# Business Engine - ProductAggregate

## Scope

This document defines the complete ProductAggregate implementation for Business Engine v1.0.
It follows CustomerAggregate (Golden Aggregate v1.0) as the official reference implementation pattern.

## Architectural compliance

- Clean Architecture:
  - domain: entity, value objects, invariants, domain event
  - application: commands/queries, ports, use cases
  - infrastructure: SQLAlchemy models/repository, event publisher, container
  - interface: API routes and DTOs
- DDD:
  - aggregate root: ProductAggregate
  - value objects: ProductExternalReference, ProductPricing
  - domain event: BusinessProductUpserted

## Business-rule justified differences from CustomerAggregate

Differences are only domain-driven:

- Uniqueness key is SKU instead of customer document.
- Product invariants include non-negative pricing.
- Product has no contact-channel invariant.

No architectural pattern differences were introduced.

## Aggregate invariants

- company_id is mandatory
- sku is mandatory and normalized (uppercase)
- name is mandatory
- unit_of_measure is mandatory
- default_cost >= 0
- default_price >= 0
- idempotency key `(company_id, source_system, source_record_id)` is unique and replay-safe

## Use cases

- UpsertProductUseCase
  - resolve existing product by external reference
  - fallback resolution by normalized SKU
  - enforce duplicate SKU prevention within tenant
  - enforce idempotency by source record + payload hash
  - replay with same payload returns existing product and does not republish event
  - replay with different payload raises idempotency conflict
  - save aggregate and publish BusinessProductUpserted event

- GetProductUseCase
  - fetch product by tenant + product_id
  - return NotFoundError when missing

## Domain Event

BusinessProductUpserted payload includes:

- event_id
- occurred_at
- company_id
- product_id
- source_system
- source_record_id
- canonical_schema_version

## SQLAlchemy adapter

Tables:

- business_products
- business_product_external_refs
- business_product_ingestion_records

Constraints:

- unique(company_id, sku)
- unique(company_id, source_system, external_id)
- unique(company_id, source_system, source_record_id)

## Security hardening

- Tenant spoofing protection enforced at HTTP routes.
- Payload/path tenant must match authenticated principal tenant.

## Concurrency hardening

- API maps SQLAlchemy IntegrityError to HTTP 409 conflict.
- Uniqueness constraints are final guard under concurrent writes.

## Request-path schema policy

- `create_all` is not used in request path.
- Schema creation belongs to migration/bootstrap lifecycle.

## Tests

- Unit tests for Product domain invariants and normalization.
- Unit tests for use-case behavior, duplicate SKU, idempotent replay and idempotency conflict.
- Integration tests for SQLAlchemy repository roundtrip and idempotency behavior.
- API hardening tests for tenant spoofing, IntegrityError mapping and create_all absence from request path.

## Boundaries

No Product implementation introduces behavior for other aggregates (Sale, Invoice, Payment, etc.).
