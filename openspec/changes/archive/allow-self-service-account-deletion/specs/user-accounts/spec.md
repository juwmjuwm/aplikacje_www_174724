# Spec Delta

## MODIFIED Requirements

### Requirement: Restricted account deletion
At `DELETE /api/users/{id}/`, an authenticated user SHALL be able to delete their own non-ADMIN account, and an ADMIN SHALL be able to delete another non-ADMIN account. Other callers SHALL receive HTTP 403. Successful deletion SHALL return HTTP 204 and invalidate the deleted account's credentials. Deletion of an ADMIN target SHALL return HTTP 409, including when the ADMIN targets their own account.

#### Scenario: Delete own account
- **WHEN** an authenticated VIEWER or PLANNER deletes their own account
- **THEN** the API returns HTTP 204, removes the account, and its credentials can no longer authorize requests

#### Scenario: Delete a viewer
- **WHEN** ADMIN deletes another current VIEWER account
- **THEN** the API returns HTTP 204 and removes that account

#### Scenario: Reject another user's deletion request
- **WHEN** a non-ADMIN user attempts to delete another user's account
- **THEN** the API returns HTTP 403 and leaves the target account unchanged

#### Scenario: Reject deletion of an administrator
- **WHEN** an ADMIN tries to delete their own account or another ADMIN account
- **THEN** the API returns HTTP 409 and leaves the ADMIN account unchanged

### Requirement: Teacher account deletion
An authenticated account holder or ADMIN SHALL be able to delete a TEACHER account with no assigned Lessons, subject to the account deletion authorization rule. The system SHALL reject deletion of a TEACHER assigned to any Lesson with HTTP 409 and preserve both the account and its Lessons, regardless of caller or other role memberships.

#### Scenario: Delete an unassigned teacher
- **WHEN** an unassigned TEACHER deletes their own account or ADMIN deletes that account
- **THEN** the API returns HTTP 204 and removes the account

#### Scenario: Delete a teacher account
- **WHEN** an assigned TEACHER or ADMIN attempts to delete that TEACHER account
- **THEN** the API returns HTTP 409 and preserves the account and all assigned Lessons

### Requirement: Safe teacher removal and account deletion
Removing TEACHER membership from a user assigned to any lesson SHALL return HTTP 409 and preserve all memberships and lessons, including when the user retains PLANNER. The same guard SHALL apply to Django Admin group editing. Account deletion through the API SHALL follow the restricted account deletion and teacher account deletion requirements. Account deletion through Django Admin SHALL remain limited to regular users with neither PLANNER nor TEACHER membership.

#### Scenario: Remove planner from an assigned teacher
- **WHEN** ADMIN removes only PLANNER from a user assigned to a lesson
- **THEN** the change succeeds and TEACHER membership and the lesson remain

#### Scenario: Remove teacher from an assigned planner
- **WHEN** ADMIN attempts to remove TEACHER from a user assigned to a lesson while retaining PLANNER
- **THEN** the request returns HTTP 409 with a reassignment or deletion explanation and leaves memberships and lessons unchanged

#### Scenario: Delete an unassigned combined-role account
- **WHEN** an unassigned PLANNER and TEACHER user deletes their own account or ADMIN deletes that account through the API
- **THEN** the API returns HTTP 204 and removes the account

#### Scenario: Delete a combined-role account
- **WHEN** an assigned PLANNER and TEACHER user or ADMIN attempts to delete that account through the API
- **THEN** the API returns HTTP 409 and preserves the account, its memberships, and its Lessons
