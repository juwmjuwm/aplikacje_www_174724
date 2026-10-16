# Tasks

## 1. Pagination

- [x] 1.1 Add a shared page-number paginator with default size 10, `size` override, cap 100, and HTTP 400 for invalid sizes; verify default, custom, capped, and invalid-size responses through API requests.
- [x] 1.2 Apply the paginator to all six scheduling viewsets and the admin user viewset; verify `count`, `next`, `previous`, stable `results`, second-page navigation, and existing authorization on every list route.
- [x] 1.3 Update the README list contract and pagination examples, including the array-to-`results` migration; verify each documented URL and response shape against the API.

## 2. Search

- [x] 2.1 Configure `search` on the five named scheduling viewsets with their specified fields; verify case-insensitive partial matches for each route, subject description matching, teacher membership exclusion, and matching `count` when combined with pagination.
- [x] 2.2 Document search fields and combined `search`, `page`, and `size` examples in the README; verify the examples return matching paginated records.

## 3. Account Names

- [x] 3.1 Require trimmed, nonblank `first_name` and `last_name` during registration and include them in the shared user response serializer; verify successful registration, field-specific HTTP 400 for missing or blank names, and names in account, role, and teacher responses.
- [x] 3.2 Allow authorized profile PATCH requests to update either name while rejecting blank names and forbidden fields; verify self and ADMIN edits, unchanged omitted fields, legacy blank-name account retrieval, and existing access restrictions.
- [x] 3.3 Update README registration, profile, and teacher examples with first and last names; verify the examples match the API and omit passwords and email.

## 4. Integration Check

- [x] 4.1 Run project checks and manually exercise search plus pagination with a VIEWER, a TEACHER, and an ADMIN; verify search and page metadata are consistent and existing read and write permissions remain in effect.
