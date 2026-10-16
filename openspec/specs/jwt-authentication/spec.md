# jwt-authentication Specification

## Purpose

Authenticate API clients with short-lived bearer access tokens and renewable refresh tokens while keeping account and role decisions current.

## Requirements

### Requirement: Token acquisition
The system SHALL issue an access token and a refresh token at `POST /api/token/` for valid credentials belonging to an active user. Username input SHALL be matched case-insensitively using the account canonicalization rule. It SHALL deny invalid or inactive credentials without revealing whether the username exists.

#### Scenario: Credential exchange
- **WHEN** an active user submits valid credentials
- **THEN** the endpoint issues an access token and a refresh token

#### Scenario: Login with uppercase username input
- **WHEN** an active user stored as `alice` submits username `ALICE` and the correct password
- **THEN** the endpoint issues an access token and a refresh token for that account

#### Scenario: Keep invalid credential responses private
- **WHEN** a client submits an unknown username or an incorrect password with any username casing
- **THEN** the endpoint denies credentials without revealing whether the username exists

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
