# user-accounts Specification

## Purpose

Provide safe self-registration and account access, with an initial administrator who can assign planning privileges to regular users.

## Requirements

### Requirement: Canonical username identity
The system SHALL accept mixed-case usernames containing only Unicode letters, Unicode decimal digits, and underscores, with no spaces or other characters. It SHALL store and return a lowercase canonical username and enforce case-insensitive uniqueness across all account creation and edit paths. The same Unicode normalization and case folding rules SHALL determine storage, conflicts, and credential lookup. The 150-character limit SHALL apply to both input and canonical values.

#### Scenario: Register with uppercase input
- **WHEN** a client registers a valid account with username `Alice`
- **THEN** the account is stored with username `alice`, and the HTTP 201 response contains `alice`

#### Scenario: Reject a case-insensitive registration duplicate
- **WHEN** an account named `alice` exists and a client registers username `ALICE`
- **THEN** the API returns HTTP 400 with a `username` error and creates no account

#### Scenario: Edit a username to mixed case
- **WHEN** a permitted caller PATCHes their own username from `alice` to `ALICE`
- **THEN** the request succeeds and the stored and returned username remains `alice`

#### Scenario: Reject a profile collision
- **WHEN** a permitted caller PATCHes an account username to a differently cased username held by another account
- **THEN** the API returns HTTP 400 with a `username` error and leaves the account unchanged

#### Scenario: Enforce uniqueness during concurrent writes
- **WHEN** concurrent account writes attempt to claim the same canonical username
- **THEN** at most one account obtains that username, and API registration or profile PATCH conflict responses identify `username` with HTTP 400

#### Scenario: Canonicalize non-API account creation
- **WHEN** an administrator account or other account is created outside the registration API with an uppercase username
- **THEN** its stored and displayed username is lowercase and cannot collide with an existing account after case-insensitive normalization

#### Scenario: Read accounts through other routes
- **WHEN** a permitted caller reads an account or teacher representation
- **THEN** its `username` value is lowercase

#### Scenario: Reject unsupported username characters
- **WHEN** a client registers or edits a username containing a space, hyphen, period, at sign, or other character outside Unicode letters, decimal digits, and underscores
- **THEN** the API returns HTTP 400 with a `username` error and leaves account data unchanged

#### Scenario: Reject unsupported username outside the API
- **WHEN** an administrator or bootstrap process attempts to create an account with an unsupported username
- **THEN** creation is rejected and no account is created

### Requirement: New password composition
New passwords SHALL contain at least eight characters, including at least one Unicode lowercase letter, one Unicode uppercase letter, one Unicode decimal digit, and one Unicode punctuation or symbol character. Whitespace SHALL NOT satisfy the special-character requirement. This policy SHALL apply to registration, self-service password changes, and supported non-API account creation or password changes. Existing password hashes SHALL remain usable until changed.

#### Scenario: Accept a composed password
- **WHEN** an account is registered with `Strong-123A` as its password
- **THEN** registration succeeds when the other account fields are valid

#### Scenario: Reject each missing password class
- **WHEN** registration or password change supplies a password shorter than eight characters or lacking any required character class
- **THEN** the API returns HTTP 400 with a password field error and leaves the account or current password unchanged

#### Scenario: Reject weak administrator credential
- **WHEN** initial administrator bootstrap or another supported non-API account creation path supplies a password that fails the policy
- **THEN** account creation is rejected without storing the weak password

#### Scenario: Preserve an existing password
- **WHEN** an existing account has a password hash created before this policy
- **THEN** its current password remains usable for authentication until it is changed

### Requirement: Letter-only personal names
Submitted `first_name` and `last_name` values SHALL be nonblank after trimming and contain only Unicode letters. Accepted values SHALL be stored and displayed with the first letter uppercase and all remaining letters lowercase. This rule SHALL apply to registration, profile edits, administrator edits, and supported non-API account creation. Existing blank names SHALL remain readable as empty strings.

#### Scenario: Capitalize names on registration
- **WHEN** a client registers with `first_name` set to `aLICJA` and `last_name` set to `nOWAK`
- **THEN** the stored and returned names are `Alicja` and `Nowak`

#### Scenario: Capitalize a profile edit
- **WHEN** a permitted caller PATCHes `last_name` to `kOWALSKA`
- **THEN** the stored and returned `last_name` is `Kowalska` and omitted fields remain unchanged

#### Scenario: Reject unsupported name characters
- **WHEN** registration or profile PATCH submits a name containing a digit, space, hyphen, apostrophe, or other non-letter character
- **THEN** the API returns HTTP 400 with an error for that name and leaves account data unchanged

#### Scenario: Normalize names outside the API
- **WHEN** an administrator or supported non-API creation path supplies valid mixed-case names
- **THEN** the names are stored and displayed in capitalized form

#### Scenario: Read a legacy blank name
- **WHEN** a permitted caller reads an existing account with an empty first or last name
- **THEN** the account remains readable and the empty name is returned as an empty string

### Requirement: Existing account format transition
Before enforcing the new username and name rules on an existing database, the system SHALL identify accounts with usernames or nonblank names that fail the new rules and stop the transition without changing account records. After invalid records are corrected, it SHALL capitalize valid existing names while preserving account IDs, credentials, privileges, memberships, and lesson references. Blank legacy names SHALL remain blank.

#### Scenario: Normalize valid existing names
- **WHEN** all existing usernames and nonblank names meet the new character rules
- **THEN** the transition capitalizes nonblank names without changing account identity, credentials, privileges, memberships, or lesson references

#### Scenario: Block invalid existing account data
- **WHEN** an existing username or nonblank name contains a disallowed character
- **THEN** the transition stops with an actionable report identifying the affected account and field, without partially changing account records

### Requirement: Existing username migration
Before enforcing canonical usernames on an existing database, the system SHALL detect accounts whose usernames become equal or invalid under the canonicalization rule. It SHALL stop migration without changing account records when either condition exists. Otherwise it SHALL canonicalize existing usernames while preserving account IDs, password hashes, privileges, memberships, and lesson references.

#### Scenario: Migrate nonconflicting usernames
- **WHEN** existing usernames have distinct canonical values
- **THEN** migration converts them to lowercase canonical values and preserves each account's identity and relationships

#### Scenario: Block conflicting usernames
- **WHEN** two existing usernames have the same canonical value
- **THEN** migration stops with an actionable report identifying the conflicting accounts so an operator can rename one before retrying, without partially changing accounts

#### Scenario: Block an invalid canonical username
- **WHEN** an existing username's canonical value exceeds the username limit or fails username syntax validation
- **THEN** migration stops with an actionable report identifying the affected account, without partially changing accounts

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
At `DELETE /api/users/{id}/`, an authenticated user SHALL be able to delete their own non-ADMIN account, and an ADMIN SHALL be able to delete another non-ADMIN account. Other callers SHALL receive HTTP 403. Successful deletion SHALL return HTTP 204 and invalidate the deleted account's credentials. Deletion of an ADMIN target SHALL return HTTP 409, including when the ADMIN targets their own account.

#### Scenario: Delete own account
- **WHEN** an authenticated VIEWER or PLANNER deletes their own account
- **THEN** the API returns HTTP 204, removes the account, and its credentials can no longer authorize requests

#### Scenario: Delete a viewer
- **WHEN** ADMIN deletes another current VIEWER account
- **THEN** the API returns HTTP 204 and removes that account

#### Scenario: Reject another user's deletion request
- **WHEN** a non-ADMIN user attempts to delete another user's account
- **THEN** the API returns HTTP 403 and leaves the target account unchanged

#### Scenario: Reject deletion of an administrator
- **WHEN** an ADMIN tries to delete their own account or another ADMIN account
- **THEN** the API returns HTTP 409 and leaves the ADMIN account unchanged

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

### Requirement: Teacher role removal
The system SHALL let ADMIN set an unassigned TEACHER back to VIEWER. It SHALL reject any change that removes TEACHER from a user assigned to a lesson with HTTP 409 and a `detail` message explaining that lessons must first be reassigned or deleted.

#### Scenario: Demote an unassigned teacher
- **WHEN** ADMIN sets an unassigned TEACHER's role to VIEWER
- **THEN** the role endpoint succeeds and the account is no longer eligible for teacher assignment

#### Scenario: Block demotion of an assigned teacher
- **WHEN** ADMIN attempts to change an assigned TEACHER to VIEWER or PLANNER
- **THEN** the endpoint returns HTTP 409 with a meaningful `detail` and leaves the role and lessons unchanged

### Requirement: Teacher account deletion
An authenticated account holder or ADMIN SHALL be able to delete a TEACHER account with no assigned Lessons, subject to the account deletion authorization rule. The system SHALL reject deletion of a TEACHER assigned to any Lesson with HTTP 409 and preserve both the account and its Lessons, regardless of caller or other role memberships.

#### Scenario: Delete an unassigned teacher
- **WHEN** an unassigned TEACHER deletes their own account or ADMIN deletes that account
- **THEN** the API returns HTTP 204 and removes the account

#### Scenario: Delete a teacher account
- **WHEN** an assigned TEACHER or ADMIN attempts to delete that TEACHER account
- **THEN** the API returns HTTP 409 and preserves the account and all assigned Lessons

### Requirement: Combined account memberships
An ADMIN SHALL be able to set a regular user's complete PLANNER and TEACHER membership set at `PATCH /api/users/{id}/role/` using `roles`, with either, both, or neither role present. An empty array SHALL represent VIEWER. Only ADMIN SHALL change memberships; registration and profile updates SHALL reject submitted privileges, and ADMIN targets SHALL remain unchangeable through this endpoint.

#### Scenario: Assign both roles
- **WHEN** ADMIN sends `{"roles":["PLANNER","TEACHER"]}` for a regular user
- **THEN** the request succeeds and the user holds both memberships on subsequent requests, including those using an existing access token

#### Scenario: Remove only planner membership
- **WHEN** ADMIN sends `{"roles":["TEACHER"]}` for a user with both memberships
- **THEN** the user retains TEACHER membership and loses PLANNER membership

#### Scenario: Reject invalid membership changes
- **WHEN** a non-ADMIN submits a role change, an ADMIN is targeted, or `roles` contains VIEWER, ADMIN, duplicates, or unknown values
- **THEN** the request is rejected without changing memberships

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

### Requirement: Safe teacher removal and account deletion
Removing TEACHER membership from a user assigned to any lesson SHALL return HTTP 409 and preserve all memberships and lessons, including when the user retains PLANNER. The same guard SHALL apply to Django Admin group editing. Account deletion through the API SHALL follow the restricted account deletion and teacher account deletion requirements. Account deletion through Django Admin SHALL remain limited to regular users with neither PLANNER nor TEACHER membership.

#### Scenario: Remove planner from an assigned teacher
- **WHEN** ADMIN removes only PLANNER from a user assigned to a lesson
- **THEN** the change succeeds and TEACHER membership and the lesson remain

#### Scenario: Remove teacher from an assigned planner
- **WHEN** ADMIN attempts to remove TEACHER from a user assigned to a lesson while retaining PLANNER
- **THEN** the request returns HTTP 409 with a reassignment or deletion explanation and leaves memberships and lessons unchanged

#### Scenario: Delete an unassigned combined-role account
- **WHEN** an unassigned PLANNER and TEACHER user deletes their own account or ADMIN deletes that account through the API
- **THEN** the API returns HTTP 204 and removes the account

#### Scenario: Delete a combined-role account
- **WHEN** an assigned PLANNER and TEACHER user or ADMIN attempts to delete that account through the API
- **THEN** the API returns HTTP 409 and preserves the account, its memberships, and its Lessons

### Requirement: Email-free account identity
The active user account model and its database table SHALL have no email field or column. Existing account IDs, usernames, password hashes, active and administrator flags, group memberships, permissions, and lesson references SHALL survive the transition; previously stored email values SHALL be removed.

#### Scenario: Migrate populated accounts
- **WHEN** the change is applied to a database containing accounts with email values and assigned teachers
- **THEN** those accounts keep their IDs, credentials, privileges, memberships, and lesson references, and the active user table has no email column

#### Scenario: Initialize an empty database
- **WHEN** the project creates a fresh database
- **THEN** it creates a usable account table without an email column

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

### Requirement: Current-user account endpoint
`GET /api/users/me/` SHALL return the currently authenticated user's account with `id`, `username`, `first_name`, `last_name`, and current `roles`. It SHALL omit password, email, and other secret or internal account fields and SHALL not require ADMIN membership.

#### Scenario: Read own account
- **WHEN** an active authenticated user requests `GET /api/users/me/`
- **THEN** HTTP 200 returns that user's `id`, `username`, `first_name`, `last_name`, and current `roles`

#### Scenario: Role change is reflected
- **WHEN** an authenticated user requests `GET /api/users/me/` after their group memberships change
- **THEN** the returned `roles` reflect their current memberships, including requests made with an existing valid access token

#### Scenario: Authentication required
- **WHEN** a caller without valid authentication requests `GET /api/users/me/`
- **THEN** the API returns HTTP 401 without account details
