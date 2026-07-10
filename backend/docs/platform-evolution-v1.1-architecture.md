# Architecture Diagram - Platform v1.1 Shared Kernel

Date: 2026-07-10

```mermaid
flowchart LR
    API[FastAPI Routers]\nCustomer/Product --> TG[TenantGuard]
    API --> EM[ErrorMapper]
    API --> TB[TransactionBoundary]
    API --> UC[Use Cases Customer/Product]

    UC --> IDS[IdempotencyService]
    UC --> HSH[CanonicalPayloadHasher]
    UC --> REP[Repositories]
    UC --> PUB[Event Publishers]

    REP --> MIX[SqlAlchemyIdempotencyMixin]
    REP --> DB[(PostgreSQL)]

    API --> CID[CorrelationIdMiddleware]
    CID --> OBS[Structured Logging Context]

    PUB --> OUTBOX[Outbox Interface]
    OUTBOX --> DISP[EventDispatcher Interface]

    subgraph Shared Kernel v1.1
      TG
      EM
      TB
      CID
      IDS
      HSH
      MIX
      OUTBOX
      DISP
    end
```

## Notes

1. Outbox/dispatcher estão prontos por contrato para evolução sem quebra.
2. Contratos REST de Customer e Product permanecem inalterados.
