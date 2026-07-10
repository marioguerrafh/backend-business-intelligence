# Auth Engine v1.0

## Scope

Auth Engine implements authentication, authorization, session management, RBAC and tenant isolation for the Business Intelligence Platform.

## Responsibilities

- Authenticate users with email and password.
- Issue JWT access and refresh tokens.
- Rotate refresh tokens and revoke previous sessions.
- Enforce role-based authorization within a tenant.
- Resolve current principal from bearer token.
- Expose auth endpoints consumed by Flutter app.

## Architecture

Layers:

- Domain: entities, roles, auth-specific errors.
- Application: use cases and port interfaces.
- Infrastructure: JWT adapter, password hasher, repositories, container wiring.
- Interface/API: HTTP schemas, dependencies and routes.

## Domain Model

- UserAccount: identity, active status and tenant memberships.
- CompanyMembership: company_id and assigned roles.
- AuthPrincipal: authenticated user context for current tenant.
- RefreshSession: refresh token lifecycle with revoke and replacement metadata.
- TokenPair: access/refresh token output contract.

## RBAC

Roles supported:

- owner
- admin
- analyst
- viewer

Role checks are evaluated against the tenant in AuthPrincipal.

## Multi-Tenant

- Tokens carry company_id claim.
- Login checks membership against requested company.
- Access and refresh flows deny tokens without tenant membership.
- Listing users is always filtered by principal company_id.

## Storage modes

- memory: in-memory repositories for local development and fast tests.
- sql: SQLAlchemy repositories with persistent users, memberships and refresh sessions.

Environment flags:

- AUTH_STORAGE_MODE=memory|sql
- AUTH_SEED_DEMO_USERS=true|false

## JWT Claims

Required claims:

- jti
- typ
- sub
- email
- company_id
- roles
- iss
- aud
- iat
- nbf
- exp

Validation rules:

- Signature validation with configured algorithm.
- Issuer and audience validation.
- Token type validation (access or refresh).

## API Endpoints

- POST /v1/auth/login
- POST /v1/auth/refresh
- POST /v1/auth/logout
- GET /v1/auth/me
- GET /v1/auth/users (owner, admin)

## Seed users (development)

- owner@acme.com / Owner@123
- analyst@acme.com / Analyst@123

## Observability

Auth use cases log security-relevant events:

- auth.login.success
- auth.refresh.success

Each log includes:

- user_id
- company_id
- correlation_id (when provided by X-Correlation-ID)

## Test Coverage

- Unit tests for login, invalid credentials, refresh rotation and expired sessions.
- Integration tests for login/me, refresh rotation, RBAC and tenant enforcement.
- Unit tests for SQLAlchemy repositories (users and refresh sessions).
