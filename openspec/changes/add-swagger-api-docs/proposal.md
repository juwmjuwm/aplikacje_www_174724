# Proposal

## Why

The project requirement calls for automatically generated OpenAPI 3.0 documentation with Swagger UI at `/api/docs/`, but the current API has no schema or browser documentation route. Developers need a current, usable description of the existing endpoints, request bodies, responses, and JWT authentication.

## What Changes

- Expose a generated OpenAPI 3.0 schema for the canonical `/api/` endpoints and Swagger UI at `/api/docs/`.
- Document JWT bearer authorization, the public token and registration operations, pagination and search parameters, and the actual request and response shapes of account actions and scheduling resources.
- Keep the `/timetables/` legacy route functional without duplicating it in the published schema.
- Add brief instructions for opening Swagger UI, acquiring a token, and authorizing requests.

## Capabilities

### New Capabilities

- `api-documentation`: Browser-accessible Swagger UI and a generated OpenAPI description of the current REST API.

### Modified Capabilities

None. The existing authentication, account, and scheduling endpoint contracts remain unchanged.

## Impact

- Adds `drf-spectacular` and its schema configuration to the Django project, plus schema and UI URLs under `/api/`.
- Adds schema metadata to account operations whose request or response differs from default serializer inference, and may add targeted metadata for other endpoints where generation is inaccurate.
- Updates API usage documentation. No database migration or endpoint behavior change is intended.
- The pinned Django 6.1.2 and DRF 3.18.3 versions are newer than the versions declared in the currently published `drf-spectacular` support list; implementation must verify that the selected release generates and serves the schema with this exact dependency set.
