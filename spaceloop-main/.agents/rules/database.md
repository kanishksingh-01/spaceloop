---
trigger: always_on
---

# Database Rules
- ORM: SQLAlchemy 2.x declarative models.
- Migrations: Explicit Alembic/SQLAlchemy schema synchronization.
- Constraints: Foreign keys, non-null guarantees, unique tokens on room QR tokens.
- Privacy: Never store raw 12-digit Aadhaar numbers (DPDP Act Section 8 compliance).
# SpaceLoop Database Rules

## Database Architecture

Use SQLAlchemy as the application's database abstraction.

Application code should not depend directly on a specific production database.

Development may use SQLite.

Production should be able to use PostgreSQL without rewriting business logic.

## Layering

Use:

Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
Database

Do not put database queries inside API routes.

## Models

Keep database models focused on persistence.

Business logic should primarily live in services/domain components.

Use relationships explicitly where appropriate.

## IDs

Use stable primary keys.

Do not expose internal database implementation details unnecessarily through public APIs.

## Constraints

Use database constraints for important invariants where appropriate:

- primary keys
- foreign keys
- unique constraints
- non-null constraints
- appropriate indexes

Do not rely only on frontend validation.

## Transactions

Use transactions for operations that must succeed or fail together.

Examples:

- booking confirmation
- payment/escrow state changes
- review creation
- critical verification state changes

## Migrations

Database schema changes must use migrations.

Do NOT manually modify production databases as the normal workflow.

Do not delete or recreate tables simply to make development tests pass.

## Indexes

Add indexes for frequently queried fields when justified.

Pay particular attention to:

- user IDs
- space IDs
- booking IDs
- booking status
- dates/times
- verification status

Do not add indexes blindly.

## Sensitive Data

Never store sensitive data unnecessarily.

Do not store raw Aadhaar information when it is not required.

Never store passwords in plaintext.

Never store secrets in database seed files.

## Images and Files

Do not store large uploaded images directly in database rows unless explicitly required.

Use object/file storage and store appropriate references/metadata in the database.

## Seed Data

Seed data must be clearly identified as development/demo data.

Do not use fake seed identities as implicit authentication.

## Schema Changes

Before changing an existing model:

1. Inspect current usage.
2. Identify dependent code.
3. Create/update migration.
4. Update relevant tests.
5. Verify existing functionality.
