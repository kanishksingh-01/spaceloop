# ADR-002: Relational Persistence Strategy
## Status: Accepted
## Context: Need ACID transactional integrity for booking lifecycles, micro-escrow holds, and telemetry audit trails.
## Decision: Use SQLAlchemy with SQLite for development/testing and PostgreSQL for high-concurrency production deployments.
