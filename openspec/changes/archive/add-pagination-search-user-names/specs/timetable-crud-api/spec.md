# Spec Delta

## ADDED Requirements

### Requirement: Paginated scheduling collections
Authenticated clients SHALL receive paginated results from `GET /api/timetables/`, `/api/lessons/`, `/api/student-groups/`, `/api/subjects/`, `/api/teachers/`, and `/api/rooms/`. Each response SHALL contain `count`, `next`, `previous`, and `results`. The default page size SHALL be 10; `page` SHALL select a page, and positive integer `size` SHALL set its size up to a maximum of 100.

#### Scenario: Default page
- **WHEN** an authenticated client lists a scheduling collection without pagination parameters and more than 10 records exist
- **THEN** `results` contains the first 10 records in a stable order, `count` is the total number of matching records, and `next` links to the next page

#### Scenario: Requested page and size
- **WHEN** an authenticated client requests `?page=2&size=25` from a collection with more than 25 records
- **THEN** `results` contains the second page of up to 25 records in the same stable order and `previous` links to the first page

#### Scenario: Size cap
- **WHEN** an authenticated client requests a `size` greater than 100
- **THEN** the response contains no more than 100 records in `results`

#### Scenario: Invalid page size
- **WHEN** an authenticated client supplies a nonnumeric, zero, or negative `size`
- **THEN** the API returns HTTP 400 with a JSON error identifying `size`

### Requirement: Searchable scheduling collections
Authenticated clients SHALL be able to use `search` on the existing timetable, student group, subject, teacher, and room list routes. Matching SHALL be case-insensitive and include partial field values. Timetables, student groups, and rooms SHALL match `name`; subjects SHALL match `name` or `description`; teachers SHALL match `first_name` or `last_name` among TEACHER members only. Search SHALL apply before pagination.

#### Scenario: Search by subject description
- **WHEN** an authenticated client requests `/api/subjects/?search=biology` and a subject description contains `Biology` while its name does not
- **THEN** that subject appears in `results` and unrelated subjects do not

#### Scenario: Search by teacher surname
- **WHEN** an authenticated client requests `/api/teachers/?search=Nowak` and a TEACHER member's `last_name` contains `Nowak`
- **THEN** that teacher appears in `results`, while a matching account without TEACHER membership does not

#### Scenario: Search with pagination
- **WHEN** an authenticated client requests a searchable collection with both `search` and `page` or `size`
- **THEN** `count`, navigation links, and `results` describe only the matching records

## MODIFIED Requirements

### Requirement: Email-free teacher directory
Authenticated callers SHALL be able to list and retrieve TEACHER members at `GET /api/teachers/` and `GET /api/teachers/{id}/`. Each teacher representation SHALL include `id`, `username`, `first_name`, `last_name`, `role`, and `roles` and SHALL omit email and passwords. Existing membership eligibility, ordering, and read-only behavior SHALL remain in effect.

#### Scenario: List a combined-role teacher
- **WHEN** an authenticated caller lists teachers and an account holds PLANNER and TEACHER memberships
- **THEN** the account appears once with both memberships, its first and last names, and no email field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated caller retrieves an ADMIN who holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles`, first and last names, and no email field
