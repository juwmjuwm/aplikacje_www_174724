# Spec Delta

## Purpose

Provide a browser-accessible reference and machine-readable OpenAPI description for the project's existing REST API so clients can discover and use its current contracts.

## ADDED Requirements

### Requirement: Browser-accessible API documentation
The system SHALL serve Swagger UI at `GET /api/docs/` and a generated OpenAPI 3.0 schema at `GET /api/schema/`. Both documentation endpoints SHALL be readable without an access token and SHALL not expose user records or credentials by themselves.

#### Scenario: Open documentation without signing in
- **WHEN** a visitor opens `/api/docs/` without an access token
- **THEN** the browser receives Swagger UI and can load the current schema from `/api/schema/`

#### Scenario: Retrieve machine-readable schema
- **WHEN** a client requests `/api/schema/` without an access token
- **THEN** the response contains an OpenAPI document whose version is in the 3.0 series

### Requirement: Canonical API operation coverage
The generated schema SHALL describe the supported `/api/` token, registration, account, timetable, lesson, student group, subject, teacher, and room operations. It SHALL show only supported HTTP methods and SHALL omit duplicate operations for the legacy `/timetables/` alias and unknown-route fallback.

#### Scenario: Inspect account and scheduling operations
- **WHEN** a reader browses the schema
- **THEN** the token and refresh endpoints, registration, password change, account role and profile actions, and supported scheduling resource methods are present under `/api/`

#### Scenario: Avoid duplicate legacy routes
- **WHEN** a reader browses the schema while the `/timetables/` alias remains routable
- **THEN** no duplicate `/timetables/` operations or wildcard fallback operation appears in the schema

### Requirement: Accurate operation contracts
The schema SHALL describe the actual request fields, response fields, status codes, pagination parameters, and search parameters of documented operations. It SHALL distinguish account profile updates, role updates, and password changes, and SHALL not present secret response fields or unsupported methods.

#### Scenario: Inspect account action bodies
- **WHEN** a reader inspects registration, profile PATCH, role PATCH, or password change in Swagger UI
- **THEN** each operation shows its accepted fields and its actual success response, including a bodyless HTTP 204 for password change

#### Scenario: Inspect resource lists
- **WHEN** a reader inspects a paginated list operation
- **THEN** the schema shows `page` and `size`, a response with `count`, `next`, `previous`, and `results`, and `search` only on lists that support it

### Requirement: JWT authorization in documentation
The schema SHALL identify protected operations as accepting bearer access tokens and SHALL identify the existing public token, token refresh, and registration operations as callable without bearer authorization. Swagger UI SHALL allow a user to enter an access token for authorized requests without changing API permissions.

#### Scenario: Call a protected operation from Swagger UI
- **WHEN** a user obtains an access token and authorizes Swagger UI with it
- **THEN** Swagger UI sends the token as bearer authorization on a protected operation and the operation applies its existing role and object permissions

#### Scenario: Inspect a public operation
- **WHEN** a reader inspects token acquisition or registration
- **THEN** the operation is shown as public and does not require a bearer token
