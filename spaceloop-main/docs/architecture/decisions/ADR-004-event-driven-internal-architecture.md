# ADR-004: Event-Driven Internal Architecture
## Status: Accepted
## Context: Decoupling booking state changes from telemetry logging and notification dispatch.
## Decision: Implement internal domain events (`BookingCreated`, `CheckinSuccess`, `CheckoutCompleted`).
