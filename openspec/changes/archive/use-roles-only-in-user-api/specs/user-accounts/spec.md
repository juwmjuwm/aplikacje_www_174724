# Spec Delta

## MODIFIED Requirements

### Requirement: Teacher role assignment
The system SHALL let ADMIN assign TEACHER to a regular user through `PATCH /api/users/{id}/role/` with `{"roles":["TEACHER"]}` or `{"roles":["PLANNER","TEACHER"]}`. Only ADMIN SHALL change roles; registration and profile updates SHALL NOT grant TEACHER.

#### Scenario: Promote a viewer to teacher
- **WHEN** ADMIN sends `{"roles":["TEACHER"]}` for an existing VIEWER
- **THEN** the role endpoint returns `roles` containing TEACHER and subsequent requests using an existing token use that membership

#### Scenario: Unauthorized teacher promotion
- **WHEN** a non-ADMIN user attempts to assign TEACHER or submits a role through registration or profile update
- **THEN** the request is rejected without changing role membership

#### Scenario: Assign teacher to another role
- **WHEN** ADMIN sends `{"roles":["PLANNER","TEACHER"]}` for an existing PLANNER
- **THEN** the user holds both memberships

#### Scenario: Reject administrator target
- **WHEN** ADMIN attempts to change an ADMIN account's roles
- **THEN** the role endpoint rejects the change without changing the account

### Requirement: Complete account role representation
Account and teacher responses SHALL contain `roles` and SHALL omit `role`. The array SHALL list PLANNER and TEACHER memberships, contain VIEWER only when a regular user holds neither, and include ADMIN plus any group memberships for an administrator.

#### Scenario: Read a combined-role account
- **WHEN** a permitted caller retrieves an account with PLANNER and TEACHER memberships
- **THEN** the response contains `roles: ["PLANNER", "TEACHER"]` and no `role` field

#### Scenario: Read an admin teacher
- **WHEN** a permitted caller retrieves an ADMIN who also holds TEACHER membership
- **THEN** the response contains ADMIN and TEACHER in `roles` and no `role` field

#### Scenario: Read a viewer
- **WHEN** a permitted caller retrieves a regular account without PLANNER or TEACHER membership
- **THEN** the response contains `roles: ["VIEWER"]` and no `role` field

### Requirement: Email-free registration and account responses
`POST /api/register/` SHALL require username, password, `first_name`, and `last_name` to create a VIEWER account subject to the existing password policy. Both names SHALL be nonblank after trimming whitespace. Registration, account list and detail, profile update, and role update responses SHALL include `id`, `username`, `first_name`, `last_name`, and `roles` while omitting `role`, email, and password. Submitted email SHALL receive HTTP 400.

#### Scenario: Register with username and password
- **WHEN** a client submits a unique username, valid password, and nonblank first and last names without email
- **THEN** the API returns HTTP 201 with `id`, `username`, `first_name`, `last_name`, and `roles: ["VIEWER"]`, and without `role`, email, or password

#### Scenario: Reject missing or blank name
- **WHEN** a registration request omits either name or supplies a name consisting only of whitespace
- **THEN** the API returns HTTP 400 with an error for the affected name field and creates no account

#### Scenario: Reject registration email
- **WHEN** a client includes `email` in a registration request
- **THEN** the API returns HTTP 400 and creates no account

#### Scenario: Read existing account with blank names
- **WHEN** a permitted caller retrieves an account created before names became required whose name fields are blank
- **THEN** the account remains retrievable and its response includes those fields as empty strings

## ADDED Requirements

### Requirement: Roles-only role updates
`PATCH /api/users/{id}/role/` SHALL require exactly one `roles` array. It SHALL reject requests containing the legacy `role` field or omitting `roles` with HTTP 400 without changing memberships. An empty array SHALL continue to set a regular account to VIEWER.

#### Scenario: Reject a legacy role request
- **WHEN** ADMIN sends `{"role":"PLANNER"}` for a regular user
- **THEN** the endpoint returns HTTP 400 and leaves memberships unchanged

#### Scenario: Reject both role fields
- **WHEN** ADMIN sends both `role` and `roles`
- **THEN** the endpoint returns HTTP 400 and leaves memberships unchanged

#### Scenario: Reject missing roles
- **WHEN** ADMIN sends a role update without `roles`
- **THEN** the endpoint returns HTTP 400 and leaves memberships unchanged

#### Scenario: Assign viewer with an empty array
- **WHEN** ADMIN sends `{"roles":[]}` for a regular user without assigned lessons
- **THEN** the request succeeds and subsequent account responses contain `roles: ["VIEWER"]`

## REMOVED Requirements

### Requirement: Compatible single-role updates
**Reason**: Single-value `role` requests are superseded by complete membership updates through `roles`.

**Migration**: Replace `{"role":"VIEWER"}` with `{"roles":[]}`, `{"role":"PLANNER"}` with `{"roles":["PLANNER"]}`, and `{"role":"TEACHER"}` with `{"roles":["TEACHER"]}`.
