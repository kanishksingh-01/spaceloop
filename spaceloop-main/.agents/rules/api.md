---
trigger: always_on
---

# API Design Rules
- RESTful standards: standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`).
- Envelope: Structured responses with status codes (`200`, `201`, `400`, `404`, `429`, `500`).
- Error Handling: Descriptive JSON error messages containing operational remediation context.
# SpaceLoop API Rules

## API Versioning

All public APIs must use versioning.

Current version:

/api/v1/

Do not introduce unversioned API endpoints for new functionality.

## Architecture

API routes/controllers must be thin.

Use:

Request
    ↓
Route
    ↓
Service
    ↓
Repository / Integration
    ↓
Database / External System

Routes must not contain substantial business logic.

## Validation

Validate all incoming data.

Validate:

- required fields
- types
- lengths
- ranges
- allowed values
- file uploads
- authorization

Never trust client-provided data.

## Authentication

Protected endpoints must require authentication.

Authentication must not be inferred from:

- frontend state
- persona selection
- URL parameters
- hidden form fields

## Authorization

Authentication does not automatically grant permission.

Every protected operation must verify the user's authorization.

Check relevant:

- role/capability
- resource ownership
- booking state
- business rules

## Responses

Use consistent response structures.

Success responses should be predictable.

Errors should provide:

- appropriate HTTP status
- stable error code
- safe human-readable message

Do not expose:

- stack traces
- database errors
- secrets
- internal implementation details

## HTTP Methods

Use HTTP methods according to operation semantics:

GET    → retrieve
POST   → create/action
PUT/PATCH → update
DELETE → delete

Do not use GET for state-changing operations.

## Pagination

Collection endpoints should support pagination when the result set can grow.

Do not return unlimited database records.

## Rate Limiting

Apply rate limiting to sensitive and expensive endpoints, especially:

- authentication
- password/reset operations
- AI endpoints
- verification
- inquiries

## API Documentation

New public API endpoints should be reflected in:

docs/api/openapi.yaml

## Compatibility

Do not break existing API behavior unnecessarily.

If a breaking change is required, document it and use versioning.
