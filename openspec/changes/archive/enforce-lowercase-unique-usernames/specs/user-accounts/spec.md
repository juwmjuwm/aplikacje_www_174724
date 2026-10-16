# Spec Delta

## ADDED Requirements

### Requirement: Canonical username identity
The system SHALL accept mixed-case usernames, store and return a lowercase canonical username, and enforce case-insensitive uniqueness across all accounts and account creation or edit paths. The same Unicode normalization and case folding rules SHALL determine storage, conflicts, and credential lookup. Existing username syntax and length limits SHALL apply to the canonical value.

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
