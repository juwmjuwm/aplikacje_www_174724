# Spec Delta

## Purpose

Authenticate API clients with short-lived bearer access tokens and renewable refresh tokens while keeping account and role decisions current.

## ADDED Requirements

### Requirement: Token acquisition
The system SHALL issue an access token and a refresh token at `POST /api/token/` for valid credentials belonging to an active user. It SHALL deny invalid or inactive credentials without revealing whether the username exists.

#### Scenario: Credential exchange
- **WHEN** an active user submits valid credentials
- **THEN** the endpoint issues an access token and a refresh token

### Requirement: Token refresh
The system SHALL accept a valid, unexpired refresh token at `POST /api/token/refresh/` and return a new access token. It SHALL deny invalid or expired refresh tokens.

#### Scenario: Refresh access
- **WHEN** a client submits a valid refresh token
- **THEN** the endpoint issues a new access token

### Requirement: Protected API access
The system SHALL require a valid access token from an active user for timetable, lesson, shared reference, and user-management API endpoints, except for public registration and token endpoints. Missing, invalid, and deactivated-user access tokens SHALL return HTTP 401. Authorized requests SHALL use current account roles and object permissions.

#### Scenario: Protected request
- **WHEN** an active user sends a valid access token to a protected endpoint
- **THEN** the request proceeds to its role and object permission checks
