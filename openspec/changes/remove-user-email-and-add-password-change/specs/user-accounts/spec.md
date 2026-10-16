# Spec Delta

## Purpose

Define username-based account identity, safe account representation, and authenticated self-service password changes without storing user email addresses.

## ADDED Requirements

### Requirement: Email-free account identity
The active user account model and its database table SHALL have no email field or column. Existing account IDs, usernames, password hashes, active and administrator flags, group memberships, permissions, and lesson references SHALL survive the transition; previously stored email values SHALL be removed.

#### Scenario: Migrate populated accounts
- **WHEN** the change is applied to a database containing accounts with email values and assigned teachers
- **THEN** those accounts keep their IDs, credentials, privileges, memberships, and lesson references, and the active user table has no email column

#### Scenario: Initialize an empty database
- **WHEN** the project creates a fresh database
- **THEN** it creates a usable account table without an email column

### Requirement: Email-free registration and account responses
`POST /api/register/` SHALL accept only username and password and create a VIEWER account subject to the existing password policy. Registration, account list and detail, profile update, and role update responses SHALL omit email and password while retaining `id`, `username`, `role`, and `roles`. Submitted email SHALL receive HTTP 400.

#### Scenario: Register with username and password
- **WHEN** a client submits a unique username and valid password without email
- **THEN** the API returns HTTP 201 with `id`, `username`, `role`, and `roles` and no email or password

#### Scenario: Reject registration email
- **WHEN** a client includes `email` in a registration request
- **THEN** the API returns HTTP 400 and creates no account

### Requirement: Username-only profile edits
The account holder or ADMIN SHALL be able to `PATCH /api/users/{id}/` to edit the username. The profile endpoint SHALL reject email, password, and privilege fields with HTTP 400 without changing the account. Existing ownership and ADMIN access rules SHALL remain in effect.

#### Scenario: Edit username
- **WHEN** a permitted caller submits a valid unique username
- **THEN** the account is updated and the response contains no email or password

#### Scenario: Reject email edit
- **WHEN** a permitted caller submits an `email` field
- **THEN** the API returns HTTP 400 without changing the account

### Requirement: Self-service password change
An authenticated account holder SHALL be able to `POST /api/users/me/password/` with `current_password` and `new_password`. The current password MUST match, and the new password MUST differ and satisfy the registration password policy. Success SHALL return HTTP 204 without secret data; invalid input SHALL return HTTP 400 without changing the password.

#### Scenario: Change own password
- **WHEN** an authenticated user supplies their correct current password and a valid different new password
- **THEN** the API returns HTTP 204, the new password authenticates, and the old password no longer authenticates

#### Scenario: Reject incorrect current password
- **WHEN** an authenticated user supplies an incorrect current password
- **THEN** the API returns HTTP 400 and leaves the current password valid

#### Scenario: Reject invalid or extra fields
- **WHEN** an authenticated user omits a required field, supplies an invalid new password, or includes an unrelated field
- **THEN** the API returns HTTP 400 without changing the password

#### Scenario: Require authentication
- **WHEN** a caller without valid authentication requests password change
- **THEN** the API returns HTTP 401 and changes no password
