---
trigger: always_on
---

# Testing Rules
- Automated Suite: Maintain 100% pass rate across the 4 core test suites.
- Determinism: Unit tests must not depend on live internet connections or paid third-party API quotas.
- Coverage: Validate boundary conditions: GPS geofence breaches, negative rates, and XSS exploits.
# SpaceLoop Testing Rules

## Testing Philosophy

Every meaningful feature change must include appropriate tests.

Do not consider a feature complete merely because the application starts.

## Test Levels

Use:

Unit tests
    → individual functions/services

Integration tests
    → database/API/module interactions

End-to-end tests
    → important user flows

Use the smallest appropriate test level for each change.

## New Backend Code

New services and important business logic should have unit tests.

New API endpoints should have integration/API tests.

## Security Testing

Authentication and authorization changes must test:

- unauthenticated access
- authenticated access
- unauthorized access
- resource ownership
- role/capability restrictions

Test that users cannot access another user's protected resources.

## AI Testing

AI-dependent functionality should have deterministic tests around:

- schema validation
- malformed output
- provider failure
- fallback behavior
- safety boundaries

Do not make tests depend unnecessarily on live LLM responses.

Mock AI providers where appropriate.

## Database Testing

Tests must not depend on production data.

Use isolated test databases/transactions/fixtures.

Do not destroy developer data to run tests.

## Regression Testing

Before modifying existing functionality:

1. Identify relevant existing tests.
2. Preserve their expected behavior unless the task intentionally changes it.

After changes, run:

1. targeted tests
2. broader relevant tests

Run the full suite when appropriate.

## Test Quality

Tests should verify behavior, not implementation details unnecessarily.

Avoid brittle tests.

Test important failure paths, not only successful cases.

## Completion Requirement

Before declaring a task complete, report:

- tests run
- tests passed
- tests failed
- known limitations

Never claim tests passed without actually running them.
