# Design

## Context

See [proposal.md](./proposal.md) for the motivation. The six scheduling collections are DRF viewsets, and the administrator user list is another DRF viewset. None has pagination or API search configured. Scheduling models have stable model ordering; teacher and user querysets order by primary key. The teacher directory is a distinct, read-only queryset of users with TEACHER membership. `User` already stores `first_name` and `last_name`; registration, profile editing, and response serializers currently omit them.

## Goals / Non-Goals

**Goals:**

- Keep the collection URLs and existing permissions while making list responses navigable and searchable where requested.
- Apply the same page contract to scheduling and administrator user lists without changing detail or mutation responses.
- Validate names at API entry points without requiring existing blank-name accounts to be migrated.

**Non-Goals:**

- Adding search to lessons or the administrator user directory.
- Changing teacher membership rules, lesson relationships, or model columns.
- Adding a separate search action or endpoint.

## Decisions

### Shared page-number pagination

Use one `PageNumberPagination` subclass for the six scheduling viewsets and the user viewset. Set the default page size to 10, use `size` as the page-size parameter, and cap it at 100. Reject nonnumeric, zero, and negative sizes with a field-specific HTTP 400 response; values above 100 are capped. Use DRF's `count`, `next`, `previous`, and `results` envelope and preserve query parameters in navigation links. Explicitly attach the paginator to these viewsets, rather than enabling it globally, so unrelated endpoints keep their current behavior. The alternative of separate paginated paths would duplicate routes and leave the existing lists unbounded.

### Per-viewset search configuration

Use DRF's search filtering only on Timetable, StudentGroup, Subject, Teacher, and Room viewsets, with `name`; `name` plus `description`; or `first_name` plus `last_name`, respectively. Keep teacher filtering inside its existing TEACHER-only queryset and apply search before pagination. Retain model ordering and primary-key tie breakers so page membership is deterministic for unchanged data. The alternative of a custom search action would repeat list and permission logic.

### Names at the serializer boundary

Add `first_name` and `last_name` to the registration serializer as required, trimmed, nonblank fields; the existing user manager accepts them through `extra_fields`. Include both names in the shared user response serializer, covering registration, account, role, and teacher responses. Permit nonblank partial edits through the profile serializer while continuing to reject unrecognized or privilege fields. Keep database fields nullable only in the existing sense of allowing blank strings, so old accounts remain readable and can be corrected through PATCH. The alternative of a database migration or global nonblank constraint would force a policy for legacy accounts outside this API change.

### Documentation and verification

Update README request and response examples for paginated lists, search, `size`, and required names. Verify the behavior with targeted API requests and existing checks. Project guidance forbids writing tests unless explicitly requested, so this change's tasks do not add tests. The separate project requirement for automated OpenAPI documentation is not satisfied by the current codebase or by README updates in this change.

## Risks / Trade-offs

- [Existing clients expect arrays or registration without names] -> Mark both changes as breaking and update examples so clients can migrate to `results` and supply names.
- [Records inserted or removed between page requests can shift page boundaries] -> Use stable ordering with a primary-key tie breaker; page-number pagination still does not provide snapshot consistency.
- [Large `size` values can make list requests expensive] -> Cap the effective page size at 100 and reject malformed sizes.
- [Legacy accounts can have empty names] -> Keep them readable and allow names to be filled in through authorized PATCH requests.

## Migration Plan

No schema or data migration is required. Deploy the API changes and update clients to read `results`, follow `next` and `previous`, and submit both names during registration. Roll back by reverting the API changes; existing account data remains compatible.
