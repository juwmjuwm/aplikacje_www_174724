# Spec Delta

## ADDED Requirements

### Requirement: Paginated administrator account directory
ADMIN SHALL receive a paginated response from `GET /api/users/` containing `count`, `next`, `previous`, and `results`. The default page size SHALL be 10; `page` SHALL select a page, and positive integer `size` SHALL set its size up to a maximum of 100. Non-ADMIN access SHALL remain forbidden.

#### Scenario: List accounts as administrator
- **WHEN** ADMIN requests `/api/users/` without pagination parameters and more than 10 accounts exist
- **THEN** `results` contains the first 10 accounts in stable order, `count` gives the total, and `next` links to the next page

#### Scenario: Choose account page size
- **WHEN** ADMIN requests `/api/users/?page=2&size=25` from a directory with more than 25 accounts
- **THEN** `results` contains the second page of up to 25 accounts and `previous` links to the first page

#### Scenario: Cap account page size
- **WHEN** ADMIN requests `/api/users/?size=200`
- **THEN** `results` contains no more than 100 accounts

#### Scenario: Reject invalid account page size
- **WHEN** ADMIN supplies a nonnumeric, zero, or negative `size`
- **THEN** the API returns HTTP 400 with a JSON error identifying `size`

#### Scenario: Preserve account list authorization
- **WHEN** a non-ADMIN user requests `/api/users/` with or without pagination parameters
- **THEN** the API returns HTTP 403 without account data

## MODIFIED Requirements

### Requirement: Email-free registration and account responses
`POST /api/register/` SHALL require username, password, `first_name`, and `last_name` to create a VIEWER account subject to the existing password policy. Both names SHALL be nonblank after trimming whitespace. Registration, account list and detail, profile update, and role update responses SHALL include `id`, `username`, `first_name`, `last_name`, `role`, and `roles` while omitting email and password. Submitted email SHALL receive HTTP 400.

#### Scenario: Register with username and password
- **WHEN** a client submits a unique username, valid password, and nonblank first and last names without email
- **THEN** the API returns HTTP 201 with `id`, `username`, `first_name`, `last_name`, `role`, and `roles` and no email or password

#### Scenario: Reject missing or blank name
- **WHEN** a registration request omits either name or supplies a name consisting only of whitespace
- **THEN** the API returns HTTP 400 with an error for the affected name field and creates no account

#### Scenario: Reject registration email
- **WHEN** a client includes `email` in a registration request
- **THEN** the API returns HTTP 400 and creates no account

#### Scenario: Read existing account with blank names
- **WHEN** a permitted caller retrieves an account created before names became required whose name fields are blank
- **THEN** the account remains retrievable and its response includes those fields as empty strings

### Requirement: Username-only profile edits
The account holder or ADMIN SHALL be able to `PATCH /api/users/{id}/` to edit `username`, `first_name`, or `last_name`. Submitted names SHALL be nonblank after trimming whitespace; omitted fields SHALL remain unchanged. The endpoint SHALL reject email, password, and privilege fields with HTTP 400 without changing the account. Existing ownership and ADMIN access rules SHALL remain in effect.

#### Scenario: Edit username
- **WHEN** a permitted caller submits a valid unique username
- **THEN** the account is updated and the response contains no email or password

#### Scenario: Edit either name
- **WHEN** an account holder or ADMIN submits a nonblank `first_name` or `last_name` through profile PATCH
- **THEN** that name is updated, the other fields remain unchanged, and the response contains both names

#### Scenario: Reject blank name edit
- **WHEN** a permitted caller submits a name consisting only of whitespace
- **THEN** the API returns HTTP 400 with an error for that field and leaves the account unchanged

#### Scenario: Reject email edit
- **WHEN** a permitted caller submits an `email` field
- **THEN** the API returns HTTP 400 without changing the account
