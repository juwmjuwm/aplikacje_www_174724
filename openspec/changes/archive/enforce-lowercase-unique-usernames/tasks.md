# Tasks

## 1. Canonical username and existing data

- [x] 1.1 Add a shared NFKC plus case-fold username canonicalizer and apply it in the user model's normal save and manager creation paths; verify mixed-case account creation stores a lowercase username and the existing database unique constraint rejects a duplicate canonical value.
- [x] 1.2 Add an atomic user-data migration that preflights collisions and invalid or overlong canonical values before changing rows; verify a nonconflicting existing account is converted without changing its ID, password hash, memberships, or lesson references, and verify a conflict aborts without partial updates.
- [x] 1.3 Document the migration preflight, manual conflict resolution, and lowercase returned name in the README; verify the instructions match the migration's actual error and retry behavior.

## 2. Registration and profile API

- [x] 2.1 Canonicalize and validate registration and profile username input before uniqueness checks, excluding the profile's current account; verify `Alice` registers as `alice`, another case variant returns HTTP 400 on `username`, and PATCHing one's own casing succeeds.
- [x] 2.2 Translate username uniqueness races at registration and profile PATCH into HTTP 400 `username` errors without hiding unrelated database errors; verify neither conflict leaves a partial account or profile change.
- [x] 2.3 Update the README registration and profile examples for mixed-case input, lowercase responses, and duplicate errors; verify the examples agree with the API behavior.

## 3. Authentication and administrator paths

- [x] 3.1 Normalize credential usernames in the shared authentication backend used by Simple JWT and Django Admin; verify an existing `alice` account can log in as `ALICE` with the correct password and invalid or inactive credentials retain their existing denial behavior.
- [x] 3.2 Canonicalize administrator bootstrap's configured username before lookup and creation and ensure Django Admin account edits use the model write path; verify repeated bootstrap does not duplicate or overwrite an existing ADMIN and Admin cannot save a case-insensitive duplicate.
- [x] 3.3 Document case-insensitive login and administrator bootstrap behavior in the README; verify documented requests and deployment steps use the implemented behavior.

## 4. Integration verification

- [x] 4.1 Run Django system and migration checks, then exercise registration, profile PATCH, token login, bootstrap, and account and teacher reads together; verify all returned usernames are lowercase, case collisions are rejected, and existing access rules still apply.
