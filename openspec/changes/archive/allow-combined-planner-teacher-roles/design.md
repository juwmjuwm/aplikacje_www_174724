# Design

## Context

See [proposal.md](./proposal.md) for motivation and the four delta specs for behavior. Django's User-to-Group relation already stores multiple memberships. Current code in `timetables/accounts.py` implements a single-role replacement endpoint, `user_role()` returns one precedence-based value, and both teacher querysets exclude PLANNER. `Lesson.clean()` also uses the scalar role value. Django Admin rejects a combined membership. The existing lesson-save and role-removal paths use `lock_teacher_assignment()` to serialize eligibility checks on SQLite.

## Goals / Non-Goals

**Goals:**
- Use current group membership as the source of truth for TEACHER eligibility and PLANNER write access.
- Give clients a complete, deterministic role representation while keeping the legacy scalar field and request form.
- Preserve atomic role changes and the assigned-teacher removal guard across API and Django Admin.

**Non-Goals:**
- Introduce a custom User model, role table, schema migration, or token-embedded role claims.
- Grant scheduling write access from TEACHER membership alone.
- Allow role changes to superuser targets through the role endpoint.

## Decisions

### Membership model and response shape

Keep Django groups for PLANNER and TEACHER and `is_superuser` for ADMIN. Introduce a shared membership helper so permission checks, teacher eligibility, deletion rules, and serialization use the same current database state. The `roles` array uses a stable order: ADMIN first for superusers, then PLANNER, then TEACHER; regular accounts with no memberships receive `["VIEWER"]`. Keep the existing `role` scalar with ADMIN > PLANNER > TEACHER > VIEWER precedence so old clients continue to parse it. For a combined-role user, `role` is PLANNER and `roles` contains both. An ADMIN who belongs to TEACHER has `role` ADMIN and `roles` containing both ADMIN and TEACHER.

Alternative considered: replace `role` with an array. That would break existing response consumers. Another alternative is to treat `role` as teacher-specific in the teacher directory; that would make the same account serialize differently across routes and hide ADMIN or PLANNER status.

### Role update request and safety

Extend the existing ADMIN-only `PATCH /api/users/{id}/role/` to accept exactly one of `role` or `roles`. `roles` is a complete replacement set containing zero, one, or both unique values from PLANNER and TEACHER; `[]` means VIEWER. Reject VIEWER or ADMIN as array items, duplicate entries, unknown entries, both fields, and missing fields with HTTP 400. Keep `role` input's current single-role replacement behavior and direct TEACHER/PLANNER switch rejection for compatibility. This includes its current assigned-teacher removal rule. For `roles`, compare actual TEACHER membership before and after the requested change; when removal would leave assigned lessons, return HTTP 409 before changing either group. Adding or removing PLANNER alone cannot remove TEACHER.

Keep the transaction and SQLite writer lock before reading membership and lesson assignments. Apply the group delta only after all checks pass. Continue rejecting superuser targets. Alternative considered: additive grant/revoke endpoints. A complete set gives clients one atomic request for both memberships and makes the empty VIEWER state clear.

### Eligibility, authorization, and Admin

Filter teacher list/detail and lesson serializer choices by TEACHER group membership only, retaining `distinct()` for the join. `Lesson.clean()` checks TEACHER membership directly. Match the Django Admin lesson picker to the same predicate. `SchedulingPermission` checks `is_superuser` or PLANNER membership for writes; reads keep their active-authenticated rule. `SafeUserChangeForm` no longer rejects PLANNER plus TEACHER but still blocks removing TEACHER from a user with lessons. Account deletion in API and Admin checks actual regular-account memberships rather than the scalar role.

Alternative considered: change `user_role()` precedence to TEACHER first. That would make combined users fail PLANNER write checks and would still leave the API and Admin exclusivity checks. A single scalar cannot represent independent capabilities.

## Risks / Trade-offs

- [A legacy client reads `role: "PLANNER"` for a combined-role teacher] -> Keep that field's established precedence and document `roles` as authoritative for membership-aware clients.
- [Removing TEACHER from an assigned combined-role user creates invalid lessons] -> Check actual membership removal under the existing write lock in both API and Admin; test that either all requested group changes commit or none do.
- [List and lesson validation disagree for an ADMIN teacher] -> Use the same TEACHER membership predicate in the directory, serializer, model, and Admin picker.
- [Historical OpenSpec deltas state exclusive roles] -> Treat this change as the newer behavior; reconcile the change history when syncing or archiving specs.

## Migration Plan

No database migration is needed. Deploy the API, model validation, Admin form, and documentation together. Existing group memberships stay intact; clients may continue sending `role` and reading `role`, while clients needing combined memberships send and read `roles`. Rollback restores the old application behavior but would leave any newly combined group memberships in the database, so remove those combined memberships or restore a predeployment backup before rolling back.
