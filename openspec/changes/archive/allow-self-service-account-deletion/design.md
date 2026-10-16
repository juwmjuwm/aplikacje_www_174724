# Design

## Context

See [proposal.md](./proposal.md) for motivation and [the account delta](./specs/user-accounts/spec.md) for the behavior contract. The existing `UserViewSet` already exposes `DELETE /api/users/{id}/`, but gives `destroy` ADMIN-only permission and restricts targets to current VIEWER accounts. `IsSelfOrAdmin` already protects account detail GET/PATCH. `Lesson.teacher` is a protected foreign key to User; lesson saves use `lock_teacher_assignment()` to coordinate teacher-related changes on SQLite.

## Goals / Non-Goals

**Goals:**

- Reuse the existing detail route and object-level authorization for account deletion.
- Return a predictable conflict response before deleting an assigned teacher or any ADMIN.
- Keep the eligibility check and hard deletion consistent with concurrent lesson assignments on the project's SQLite database.

**Non-Goals:**

- Change role management, lesson assignment rules, or Django Admin's account-deletion policy.
- Add a database migration or a second deletion route.

## Decisions

### Use the existing detail permission

Keep list and role actions ADMIN-only. Apply `IsAuthenticated` and `IsSelfOrAdmin` to destroy, as for detail GET/PATCH, and use `get_object()` so DRF checks target ownership before deletion. This avoids a second authorization implementation and preserves HTTP 403 for a non-ADMIN caller targeting another account. An unauthenticated caller remains rejected by authentication.

Alternative: introduce `DELETE /api/users/me/`. That would duplicate the existing detail route and leave ADMIN deletion on a different path.

### Check the target under a transaction before deleting

Inside one atomic block, call `lock_teacher_assignment(target_id)` before reading the target again and checking its current state. Reject `is_superuser` targets with HTTP 409, regardless of caller. Query for assigned Lessons before deleting a TEACHER target and return HTTP 409 with a clear reassignment or deletion message when any exist. Otherwise hard-delete the target and return HTTP 204. Role membership does not otherwise affect eligibility, so PLANNER and unassigned TEACHER accounts require no role change. Keep `Lesson.teacher` on `PROTECT` as a backstop; translate a protected-deletion failure into HTTP 409 if it occurs.

On SQLite, `lock_teacher_assignment()` takes the writer lock before the assignment check, aligning deletion with lesson saves and role changes. The account row re-read keeps the decision based on current state. Alternative: rely only on `select_for_update()`, which SQLite ignores and cannot serialize the assignment check there.

### Keep Django Admin deletion behavior separate

The request changes the API endpoint. The existing Django Admin policy permits deletion only for VIEWER accounts and remains unchanged. The account spec delta states this distinction explicitly.

## Risks / Trade-offs

- [Existing clients may assume only VIEWER accounts can be deleted] -> Update README guidance and preserve the same path, HTTP 204 success, and conflict semantics for protected targets.
- [A lesson is assigned while deletion is checking eligibility] -> Acquire the SQLite writer lock before checking, keep the check and deletion atomic, and retain foreign-key protection as a final safeguard.
- [Deletion removes access immediately] -> Keep the existing hard-delete behavior and verify that a deleted account cannot authorize another protected request.

## Migration Plan

No schema migration is needed. Deploy the endpoint and documentation together. Rollback restores the prior permission and eligibility checks; already deleted accounts cannot be recovered without a database backup.
