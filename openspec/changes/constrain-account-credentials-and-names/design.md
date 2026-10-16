# Design

## Context

See [proposal.md](./proposal.md) for motivation and [specs/user-accounts/spec.md](./specs/user-accounts/spec.md) for the behavior contract. The API already routes username validation through `accounts.usernames.validate_username` and password checks through Django's password validator framework. `User.save` canonicalizes usernames, while names are currently trimmed only by API serializers. Django Admin and bootstrap use separate creation paths. An earlier username migration imports the live validator, so changing that validator could change the behavior of historical migrations on a fresh database.

## Goals / Non-Goals

**Goals:**

- Keep validation consistent across API, Django Admin, bootstrap, and manager-backed creation.
- Preserve existing password hashes, account IDs, and relationships during deployment.
- Keep historical migrations reproducible after changing the live username validator.

**Non-Goals:**

- Validate passwords at login or force existing users to reset them.
- Change the 150-character username limit or existing canonicalization and uniqueness behavior.
- Require names for legacy accounts or bootstrap accounts that have no names configured.
- Attempt to police direct database writes that bypass application validation.

## Decisions

1. **Use shared Unicode-aware field validators.** Username validation checks each input character and its NFKC/casefold canonical value for `isalpha`, `isdecimal`, or underscore. It retains the 150-character checks. Name validation trims and accepts only `isalpha` characters, then applies Python capitalization before persistence. The model and Admin forms use these helpers; API serializers convert their errors to field-specific HTTP 400 responses. This avoids slightly different regular expressions in each entry point. ASCII-only validation was considered, but would reject valid names and usernames containing Polish letters.

2. **Use the password validator framework plus creation-path checks.** Add a composition validator to the existing Django validator list; keep the existing minimum length, similarity, common-password, and numeric-password checks. Treat Unicode punctuation and symbols as special characters, excluding whitespace. Registration and password change already call the framework. Manager-backed account creation, bootstrap, and Admin creation or password editing must invoke it before storing a new password. Existing hashes are never revalidated when authenticating or saving unrelated fields. A serializer-only rule was rejected because non-API accounts would bypass it.

3. **Use a preflight data migration for existing accounts.** The migration first scans every row and reports IDs and offending fields for any username or nonblank name violating the new syntax. If any exist, it raises an actionable error before updates. Otherwise, it capitalizes nonblank names and preserves blank names. The scan and update run atomically. Operators correct invalid records and retry. Automatic replacement of disallowed characters was rejected because it can alter identities or create collisions. The previous username migration must use its historical validation rules rather than importing the new live helper.

4. **Enforce at supported write boundaries.** API and Admin reject invalid submitted names, including empty values. The model normalizes valid nonblank names on save so manager-backed creation has the same stored format; legacy or bootstrap blank names remain allowed. The account representation reads stored names, with the migration bringing valid legacy values into canonical form. Direct bulk updates remain a documented bypass and are outside this change.

## Risks / Trade-offs

- Existing usernames or names with punctuation can block deployment → report each affected account and field before mutation; correct records while preserving account IDs and relations.
- Stricter passwords can reject current bootstrap configuration → validate the configured password before creating the initial ADMIN and provide a clear command error.
- Unicode casing can change string length in unusual cases → validate canonical username length and name field length after normalization.
- Historical migration imports can silently change fresh-install behavior → freeze the old validator semantics in the historical migration before changing the live helper.

## Migration Plan

1. Deploy the new preflight/capitalization migration with the validators and account path changes. Run migration before restarting account writers.
2. If the migration reports invalid rows, correct those values and rerun it. Preserve the database backup for rollback.
3. Existing password hashes remain accepted; only newly set passwords use the composition rule. On rollback, restore the application and database backup if name capitalization must be undone.
