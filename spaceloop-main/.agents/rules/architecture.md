---
trigger: always_on
---

# Architecture Rules
- Pattern: Modular Monolith with Domain-Driven Design (DDD).
- Boundaries: Modules in `backend/modules/` communicate via well-defined service interfaces or domain events.
- Zero-Hardware Access: Physical access relies entirely on software layers (GPS radar <50m, QR passes, dynamic PINs).
- Unidirectional Dependency: Domain -> Database/Modules -> API Layer.

# SpaceLoop Architecture Rules

## Core Architecture

SpaceLoop uses a modular monolith architecture.

Do NOT introduce microservices unless explicitly requested.

The existing SpaceLoop functionality must be preserved during migration.

Prefer incremental refactoring over large rewrites.

## Backend Layers

Use this dependency flow:

API / Routes
    ↓
Services
    ↓
Repositories
    ↓
Database

Routes must NOT contain business logic.

Services contain business rules and orchestration.

Repositories handle database persistence.

## Module Boundaries

Keep major functionality separated into modules:

- auth
- users
- spaces
- discovery
- bookings
- leases
- payments
- verification
- access
- inspections
- trust
- inquiries
- notifications

Do not place unrelated functionality into another module simply for convenience.

## AI Boundary

Feature modules must NEVER call Groq or Gemini directly.

All LLM calls must go through:

backend/ai/router.py

AI providers must remain replaceable.

## Database

Use SQLAlchemy for database access.

Do not place raw SQL inside API routes or service logic unless there is a documented reason.

## Existing Code

The current SpaceLoop application is an existing working system.

When migrating:

1. Inspect existing behavior first.
2. Preserve working functionality.
3. Move/refactor code incrementally.
4. Do not rewrite working functionality without a reason.
5. Do not delete existing functionality merely because it is not yet migrated.

## Changes

Before making architectural changes:

- inspect the relevant existing implementation
- inspect docs/architecture/
- inspect applicable .agents/rules/
- identify dependencies between modules

Make the smallest safe change that satisfies the task.
