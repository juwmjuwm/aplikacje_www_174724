# Spec Delta

## MODIFIED Requirements

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
