# Proposal

## Why

The existing user deletion endpoint is limited to ADMIN callers and VIEWER targets. Account holders need to be able to delete their own accounts, and role membership alone should not prevent deletion when the account has no protected lesson assignment.

## What Changes

- **BREAKING** Permit an authenticated account holder to delete their own regular account at `DELETE /api/users/{id}/`; retain ADMIN deletion of other regular accounts.
- **BREAKING** Permit deletion of PLANNER, unassigned TEACHER, and unassigned combined-role accounts without first changing their roles.
- Reject deletion of any ADMIN account, including an ADMIN's own account, and reject deletion of any TEACHER assigned to a Lesson, regardless of caller.
- Update the account deletion documentation and verify the authorization and protected-assignment behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-accounts`: Change the existing deletion permission and target-eligibility requirements while preserving assigned-teacher protection.

## Impact

- `DELETE /api/users/{id}/` changes authorization and role eligibility; successful deletion remains HTTP 204 and blocked deletions remain HTTP 409 or 403 as appropriate.
- The affected implementation is the user viewset and its permission flow; Lesson's protected teacher relation remains in place.
- The user account spec and README deletion guidance need updates. No model migration or new dependency is expected.
