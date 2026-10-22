# Spec Delta

## ADDED Requirements

### Requirement: Current-user account endpoint
`GET /api/users/me/` SHALL return the currently authenticated user's account with `id`, `username`, `first_name`, `last_name`, and current `roles`. It SHALL omit password, email, and other secret or internal account fields and SHALL not require ADMIN membership.

#### Scenario: Read own account
- **WHEN** an active authenticated user requests `GET /api/users/me/`
- **THEN** HTTP 200 returns that user's `id`, `username`, `first_name`, `last_name`, and current `roles`

#### Scenario: Role change is reflected
- **WHEN** an authenticated user requests `GET /api/users/me/` after their group memberships change
- **THEN** the returned `roles` reflect their current memberships, including requests made with an existing valid access token

#### Scenario: Authentication required
- **WHEN** a caller without valid authentication requests `GET /api/users/me/`
- **THEN** the API returns HTTP 401 without account details
