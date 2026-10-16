# Proposal

## Why

Current account validation permits username punctuation and unconstrained name characters, and the password policy does not require each requested character class. This allows account data that does not match the intended format across API and non-API creation paths.

## What Changes

- **BREAKING** Restrict new or edited usernames to Unicode letters, Unicode decimal digits, and underscores while retaining lowercase canonical storage, the 150-character limit, and case-insensitive uniqueness.
- **BREAKING** Require new passwords to have at least eight characters and at least one lowercase letter, uppercase letter, decimal digit, and special character for registration, password changes, and account creation outside the API.
- **BREAKING** Require submitted first and last names to contain Unicode letters only after trimming; save and return them in capitalized form.
- Check existing usernames and names before enforcement, normalize valid existing names, and provide a path to correct invalid records without losing account identity or relationships. Existing password hashes remain valid until the password is changed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-accounts`: Define exact username, password, and personal-name rules across account entry points and existing data.

## Impact

- Account model, username and password validators, API serializers, Django Admin forms, bootstrap command, and account migration handling.
- Registration, profile PATCH, password change, and administrator creation can reject inputs previously accepted.
- Account API responses and admin displays use capitalized names.
- README account examples and deployment guidance need updating.
