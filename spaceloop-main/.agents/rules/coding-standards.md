---
trigger: always_on
---

# Coding Standards
- Python: Strictly adhere to PEP 8, typing annotations where appropriate, and clean exception handling.
- TypeScript / React: Use strict typing, functional components, hooks, and feature-sliced architecture.
- Immutability: Prefer immutable value objects for financial calculations and telemetry tokens.
# SpaceLoop Coding Standards

## General

Write clear, maintainable code.

Prefer simple solutions over clever solutions.

Do not introduce abstractions without a practical reason.

Follow the existing project conventions when they are compatible with the architecture rules.

## Python

Use Python 3.11+ compatible code unless the project specifies otherwise.

Follow PEP 8.

Use type hints for new code.

Prefer explicit names over abbreviations.

Example:

GOOD:
calculate_booking_price()

AVOID:
calc_bp()

## Functions

Functions should have one clear responsibility.

Avoid unnecessarily large functions.

Extract reusable logic when it improves clarity.

## Classes

Classes should have clear responsibilities.

Do not create classes simply to wrap a single trivial function.

## Imports

Keep imports organized.

Avoid circular dependencies.

Use the architectural dependency direction defined in architecture.md.

## Error Handling

Handle expected errors explicitly.

Do not use broad exception handling such as:

except Exception:
    pass

Never silently swallow errors.

## Logging

Use the project's logging system.

Do not use print() for application logging.

Never log:

- passwords
- tokens
- API keys
- raw Aadhaar data
- identity documents
- sensitive authentication information

## Configuration

Do not hardcode environment-specific values.

Use configuration/environment variables.

Never hardcode secrets.

## Comments

Write comments when they explain WHY something exists.

Do not add comments that merely restate obvious code.

## Naming

Use descriptive names.

Python:

snake_case

Classes:

PascalCase

Constants:

UPPER_SNAKE_CASE

## Dependencies

Do not add a dependency when the existing project already provides the required capability.

Before adding a package:

1. Check whether an existing dependency can solve the problem.
2. Check whether the package is necessary.
3. Keep the dependency focused and maintained.

## Refactoring

Do not perform unrelated refactoring while implementing a feature.

Preserve existing behavior unless the task explicitly requires changing it.

## Code Quality

Before finishing:

- remove unused imports
- remove dead code introduced by the change
- check type errors where applicable
- check linting where configured
- run relevant tests
