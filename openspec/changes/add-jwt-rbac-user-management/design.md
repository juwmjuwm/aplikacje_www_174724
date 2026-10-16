# Design

## Context

The six scheduling models, DRF serializers, and `ModelViewSet` routes already exist. There is no JWT configuration, registration flow, role policy, or API test coverage. `Timetable.owner` is non-nullable and writable through the serializer; Admin displays and filters it. The API router has a catch-all 404 route, so new account and token paths must be registered before that catch-all. See the proposal for motivation and the three specs for observable behavior.

## Goals / Non-Goals

**Goals:**

- Use JWT bearer tokens without server-side sessions for API authentication, while reading current account state for authorization.
- Keep role decisions simple with Django's existing User model and permissions enforced consistently across all six scheduling viewsets.
- Preserve existing timetables and lessons while removing the owner column.

**Non-Goals:**

- Per-timetable sharing, a custom User model, or an audit log of timetable creators.
- Password reset and email verification workflows.
- OpenAPI, pagination, search/filter, and dedicated scheduling analytics endpoints; these remain separate requirements work.

## Decisions

### JWT authentication and signing configuration

Add `djangorestframework-simplejwt`, configure DRF's `JWTAuthentication`, and register token obtain and refresh paths before the API catch-all. Protect application API viewsets by default and allow anonymous access only to registration and token endpoints. Use the database-backed JWT authentication class, not its `TokenUser` variant, so requests see account deactivation and current group membership. Do not authorize from role claims in the token. Use a deployment-provided `DJANGO_SECRET_KEY` rather than the currently committed development key, because SimpleJWT's default signing key follows Django's secret key. Load local `.env` values from an ignored file and provide a placeholder `.env.example` without real secrets. Keep Django Admin's existing session flow separate.

Alternative: encode roles in access tokens and use stateless user objects. That avoids a user lookup but delays demotion until tokens expire and does not fit the current-role requirement.

### Roles and custom permissions

Represent ADMIN with Django `is_superuser`; represent PLANNER with membership in a `PLANNER` group; all other active regular users are VIEWER. Only a bootstrap process can create ADMIN in this change. Implement custom DRF `BasePermission` classes: one for authenticated read versus planner/admin writes, one for ADMIN-only role management and deletion, and `IsSelfOrAdmin` with `has_object_permission()` comparing the target User primary key to `request.user.pk`. Use the ownership class on user detail GET/PATCH and call object permission checks if a custom lookup bypasses DRF's generic `get_object()` flow. Permit user list only to ADMIN. Expose role changes through a separate detail action, never through the profile serializer. Reject unauthorized fields rather than silently ignoring them.

Handle `DELETE /api/users/{id}/` separately from self-service profile access: require ADMIN, then check the target's current effective role immediately before deletion. Hard-delete only VIEWER users; return HTTP 409 for PLANNER or ADMIN targets. After ADMIN demotes a PLANNER through the role action, the account becomes eligible for deletion. A VIEWER or PLANNER cannot delete their own account. Since API authentication resolves the database user on each request, tokens belonging to a deleted account cease to authorize protected requests. Keep the role check and delete in one database transaction so a concurrent role update cannot bypass the eligibility rule.

Alternative: a role field on a new custom User model. That creates a disruptive auth-model migration after Django's default User and timetable FK are already in use; existing flags and a group suffice for three mutually exclusive effective roles.

### Registration and bootstrap

Add a public registration serializer accepting username, password, and optional email. Validate the password with Django's configured validators and use `create_user()` so only a password hash is stored. Reject privilege fields and return no password. Keep profile updates to username and email. Use a dedicated idempotent management command invoked after `migrate` during deployment startup to create the `PLANNER` group and initial ADMIN from `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` in the environment. The command fails clearly if required bootstrap credentials are absent when no ADMIN exists; on later runs it never resets an existing account or silently elevates a same-named regular user. Do not query or write the database from `AppConfig.ready()`.

Alternative: create the account inside `AppConfig.ready()` or a data migration. The former runs before tables may exist and during unrelated commands; the latter should not embed or depend on deployment secrets.

### Scheduling authorization and owner removal

Apply the scheduling permission class to the shared viewset base so every timetable, lesson, student group, subject, teacher, and room route has the same role policy. Preserve existing validation and protected deletion. Remove `owner` from `Timetable`, its serializer, and Admin configuration. Explicitly reject incoming `owner` keys on POST, PUT, and PATCH, because a default DRF serializer can otherwise ignore unknown input. Create a schema migration that drops only the owner column. The prior completed change specs describe owner-required behavior, so reconcile them before syncing or archiving the overall specification history.

Alternative: retain `owner` as creator metadata but ignore it for access. The user explicitly chose to remove it, and retaining a non-authoritative owner would leave API and data semantics ambiguous.

## Risks / Trade-offs

- [Dropping the owner column discards existing owner IDs] -> Back up SQLite before migration and document the breaking API change; timetable and lesson rows remain.
- [A public registration endpoint can be abused] -> Enforce password validation and consider rate limiting at deployment. No new account can choose a privileged role.
- [A committed signing secret would permit forged JWTs] -> Require a deployment secret from environment and keep `.env` ignored.
- [A role change may leave previously issued refresh tokens usable] -> Permissions read the current database role on every protected request, so refresh cannot restore old planner rights. Inactive accounts are rejected on protected requests.
- [Deleting a user is irreversible and invalidates their credentials] -> Restrict deletion to ADMIN and current VIEWER targets, block PLANNER/ADMIN targets with HTTP 409, and document the required demotion step.
- [The API catch-all can shadow new paths] -> Register token and account routes before the catch-all and test all paths.
- [Direct Django Admin or shell edits can bypass API permission classes] -> Keep API policy explicit; Django Admin requires superuser/staff authorization separately.

## Migration Plan

1. Add dependencies and environment configuration, then back up the existing SQLite database before dropping `Timetable.owner`.
2. Apply the owner-removal migration, preserving timetable and lesson records. The old non-nullable owner column cannot be restored from the new schema without backup data; rollback requires restoring the database backup and previous code.
3. Run migrations, then invoke the idempotent bootstrap command before serving requests. Document required environment variables and the one-time ADMIN behavior.
4. Roll out protected routes and client changes together; clients must stop sending or expecting `owner` and obtain JWTs before calling protected APIs.
5. Run system checks, migration checks, API tests, and representative end-to-end requests for registration, token refresh, role changes, and scheduling permissions.
