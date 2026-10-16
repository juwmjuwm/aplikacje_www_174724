# Spec Delta

## Purpose

Provide safe self-registration and account access, with an initial administrator who can assign planning privileges to regular users.

## ADDED Requirements

### Requirement: Public viewer registration
The system SHALL accept username and password at `POST /api/register/` without authentication and create an active VIEWER account with a securely stored password. It SHALL reject duplicate usernames, invalid credentials, and submitted privilege fields with HTTP 400. Successful registration SHALL return HTTP 201 with non-secret account details.

#### Scenario: Register a user
- **WHEN** a client submits a unique username and valid password
- **THEN** the API creates an active VIEWER account

### Requirement: Initial administrator
The system SHALL create one ADMIN account from deployment-provided credentials during initial database setup, without overwriting that account's password or privileges on later starts. The password SHALL be stored securely.

#### Scenario: Initial setup
- **WHEN** migrations are complete and no ADMIN exists
- **THEN** bootstrap creates an ADMIN from deployment credentials

### Requirement: Owned account profile
The system SHALL expose `GET` and `PATCH /api/users/{id}/` to the account holder and ADMIN, with editable profile fields limited to username and email. A custom object permission SHALL check whether the requested account belongs to the caller or the caller is ADMIN. Other users SHALL receive HTTP 403. Privilege and password fields SHALL be rejected without changing them.

#### Scenario: Edit own profile
- **WHEN** an account holder updates their username or email
- **THEN** the API saves the change and returns non-secret profile data

### Requirement: Administrator role management
The system SHALL let ADMIN list users at `GET /api/users/` and set a regular user's role to VIEWER or PLANNER at `PATCH /api/users/{id}/role/`. Role changes SHALL affect subsequent requests, including requests using previously issued access tokens. Non-admin callers SHALL receive HTTP 403, and ADMIN targets SHALL retain their role.

#### Scenario: Change a regular user's role
- **WHEN** ADMIN sets a regular user's role to PLANNER or VIEWER
- **THEN** subsequent requests use the updated role

### Requirement: Restricted account deletion
The system SHALL allow only ADMIN to delete a VIEWER account at `DELETE /api/users/{id}/`, returning HTTP 204 and invalidating that account's credentials. It SHALL return HTTP 409 for PLANNER and ADMIN targets and HTTP 403 for non-admin callers. A PLANNER must first be changed to VIEWER through the role endpoint.

#### Scenario: Delete a viewer
- **WHEN** ADMIN deletes a current VIEWER account
- **THEN** the account is removed and can no longer authenticate
