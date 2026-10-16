# Tasks

## 1. Username rules and migration safety

- [ ] 1.1 Freeze the existing username validation semantics inside the historical canonical-username migration; verify a fresh migration still accepts usernames permitted by that migration's original rule.
- [ ] 1.2 Restrict the shared username validator and model/Admin field metadata to Unicode letters, decimal digits, and underscores while preserving NFKC/casefold, uniqueness, and length behavior; verify registration, profile PATCH, Admin, and bootstrap reject punctuation and spaces with the expected field or command errors.
- [ ] 1.3 Document the new username syntax in README and verify its examples use only accepted characters.

## 2. Password rules

- [ ] 2.1 Add the composition validator to the existing password policy and invoke the policy for manager-backed creation, bootstrap, and Admin password writes; verify short passwords and passwords missing each required class are rejected while a valid composed password is accepted.
- [ ] 2.2 Verify registration and self-service password change return field-specific HTTP 400 errors for invalid new passwords, preserve the old password after failure, and still authenticate existing hashes.
- [ ] 2.3 Update README password and bootstrap guidance and verify its example passwords satisfy every required class.

## 3. Names and existing accounts

- [ ] 3.1 Add shared Unicode letter-only name validation and capitalization at API, Admin, and model-backed write boundaries; verify mixed-case names are saved and returned capitalized, invalid names receive field errors, and omitted profile fields remain unchanged.
- [ ] 3.2 Add an atomic preflight/capitalization migration for existing accounts, preserving blank names and relationships; verify invalid rows produce an actionable account-and-field report without partial updates, and valid rows capitalize successfully.
- [ ] 3.3 Update README name rules and transition instructions; verify the documented examples and remediation steps match the implemented behavior.
