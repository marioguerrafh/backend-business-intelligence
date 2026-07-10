# Business Engine - CustomerAggregate

## Scope

This document defines the complete CustomerAggregate implementation for Business Engine v1.0.
Only CustomerAggregate is implemented at this stage.

## Architectural compliance

- Clean Architecture:
  - domain: entities, value objects, invariants, domain events
  - application: commands/queries, ports, use cases
  - infrastructure: SQLAlchemy models and repository adapter, event publisher
  - interface: API routes and DTOs
- DDD:
  - aggregate root: CustomerAggregate
  - value objects: BillingAddress, ContactChannel, ExternalReference
  - domain event: BusinessCustomerUpserted

## Aggregate invariants

- company_id is mandatory
- legal_name is mandatory
- active customer requires at least one contact channel
- document_number is normalized and unique by tenant (company_id)
- idempotency key `(company_id, source_system, source_record_id)` is unique and replay-safe

## Use cases

- UpsertCustomerUseCase
  - resolve existing customer by external reference
  - fallback resolution by normalized document number
  - enforce duplicate document prevention within tenant
  - save aggregate and publish BusinessCustomerUpserted event
  - enforce idempotency by source record with payload hash
  - replay with same payload returns existing customer and does not publish duplicate event
  - replay with different payload raises idempotency conflict

- GetCustomerUseCase
  - fetch customer by tenant + customer_id
  - return NotFoundError when missing

## Domain Event

BusinessCustomerUpserted payload includes:

- event_id
- occurred_at
- company_id
- customer_id
- source_system
- source_record_id
- canonical_schema_version

## SQLAlchemy adapter

Tables:

- business_customers
- business_customer_contacts
- business_customer_external_refs
- business_customer_ingestion_records

Constraints:

- unique(company_id, document_number)
- unique(company_id, source_system, external_id)
- unique(company_id, source_system, source_record_id)

## Security hardening

- Tenant spoofing protection is enforced in HTTP routes:
  - company_id in request must match authenticated principal company_id.
  - cross-tenant reads/writes return 403.

## Concurrency hardening

- API maps SQLAlchemy IntegrityError to HTTP 409 conflict.
- Uniqueness constraints remain the final guard against concurrent writes.

## Request-path schema policy

- `create_all` was removed from request path.
- Schema creation must happen in migration/bootstrap workflow.

## Tests

- Unit domain invariants and value behavior
- Unit use case behavior and event emission
- Integration test with SQLAlchemy adapter roundtrip

## Boundaries

No code for Product, Sale, Invoice, Payment, Supplier, Inventory or FinancialAccount is included.
