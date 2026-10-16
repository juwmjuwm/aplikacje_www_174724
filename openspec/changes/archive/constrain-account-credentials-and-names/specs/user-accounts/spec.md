# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
