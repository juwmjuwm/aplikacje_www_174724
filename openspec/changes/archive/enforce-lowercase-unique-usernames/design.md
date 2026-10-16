# Design

## Context

See [proposal.md](./proposal.md) for the motivation and the account and authentication deltas for the behavior contract. The custom `User` inherits Django's `AbstractUser` username field, which already has a database `unique=True` constraint. `UserManager.create_user()` applies Django's Unicode normalization, but profile PATCH saves through a model serializer and does not apply the same normalization. The project uses SQLite, DRF model serializers, Simple JWT's default token view, and Django Admin. Bootstrap compares its configured administrator username with stored values using an exact lookup.

## Goals / Non-Goals

**Goals:**

- Use one canonicalization function for all username entry points and credential lookup.
- Keep the existing username column and unique constraint as the final concurrency boundary.
- Migrate existing account names without changing account identity or relationships.

**Non-Goals:**

- Changing password policy, role rules, account permissions, or token format.
- Automatically deciding which account keeps a colliding legacy name.
- Providing case-insensitive search for the administrator or teacher directories.

## Decisions

### Canonical stored username

Define one function that first applies Django's NFKC username normalization and then Unicode `casefold()`. Store that result as `User.username`; return the stored value in every account and teacher representation. Case folding gives Unicode-aware case-insensitive identity, including characters that SQLite's built-in `LOWER` and `NOCASE` do not handle. Validate both the submitted and canonical values against the existing username syntax and 150-character limit, since folding can expand a value. The alternative of SQLite `NOCASE` or a functional `LOWER(username)` index would cover ASCII but not all usernames accepted by Django's Unicode username validator. A second unique key column would duplicate the value when the canonical name itself can serve as the unique key.

### One account write boundary

Canonicalize in the user model's normal save path so registration, `create_user`/`create_superuser`, profile PATCH, and Django Admin persist the same form. Keep explicit username validation in the registration and profile serializers after canonicalization so normal collisions return a field-keyed HTTP 400. Exclude the current instance from profile collision checks, allowing a user to submit their own name in a different case. Convert a database uniqueness race in these two API paths into the same `username` HTTP 400 response, and avoid changing other `IntegrityError` handling. Update bootstrap's initial username lookup to canonicalize its environment value before comparing or creating. Direct bulk updates and raw SQL that bypass model saves must use the same canonicalization function; no application path currently writes usernames that way. Relying only on serializer validation was rejected because it misses Admin, bootstrap, and concurrent API writes.

### Credential lookup

Normalize the submitted username before the authentication backend looks it up. Use that backend for Simple JWT token acquisition and Django Admin login, keeping password checks and invalid-credential responses as they are. This lets a user authenticate with the mixed-case value they originally submitted. Refresh tokens remain ID-based and need no change. Normalizing only the token serializer was rejected because Django Admin would then use a different rule.

### Existing data migration

Use an atomic data migration to compute every account's canonical username before making updates. If two accounts map to one value, or a canonical value fails the username length or syntax limits, raise a clear migration error identifying the affected account IDs and current names; leave all rows unchanged. An operator must rename conflicting accounts and rerun migration. Otherwise update usernames to their canonical values. Account primary keys and related foreign keys stay intact. A silent winner or suffix assignment was rejected because it would change a person's login identity without a deliberate decision.

### Documentation and verification

Document mixed-case registration, PATCH, token login, lowercase responses, and migration conflict resolution in the README. Verify the flows with targeted read/write API and Admin checks during implementation, including a duplicate request and an existing mixed-case account. Project guidance excludes adding automated tests unless the user explicitly requests them.

## Risks / Trade-offs

- [Case folding can expand or change Unicode spelling, such as `ß` to `ss`] -> Validate the canonical value and document that the returned username is authoritative.
- [Existing case-colliding accounts block deployment] -> Preflight all account names before updating any row and report conflicts for explicit resolution.
- [Validation can race another account write] -> Keep the database unique constraint and translate its username conflict to the API's field error.
- [Bulk SQL bypasses model normalization] -> Keep username changes in the model/manager/Admin/API paths and document the shared canonicalization requirement for any later bulk import.

## Migration Plan

1. Before deployment, inspect existing accounts for canonical collisions and overlong canonical names using the same normalization algorithm; resolve any reported accounts deliberately.
2. Apply the atomic data migration, then deploy canonicalization at all account write and login paths. Existing user IDs, passwords, roles, memberships, and lesson references remain unchanged.
3. Update clients to use lowercase returned usernames. Mixed-case username input remains accepted.
4. Rollback requires restoring prior application code and, if original username casing matters, a database backup: the migration intentionally does not preserve original casing.
