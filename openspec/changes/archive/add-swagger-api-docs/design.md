# Design

## Context

See `proposal.md` for the motivation and `specs/api-documentation/spec.md` for the observable contract. Django REST Framework currently uses SimpleJWT and a global authenticated default. The project routes account endpoints directly, schedules resources through routers, and exposes the scheduling URL set twice: at `/api/` and `/timetables/`. The scheduling URL set ends with a wildcard 404 handler. `UserViewSet` uses `UserSerializer` for reads but `ProfileSerializer` and `RoleSerializer` for two PATCH operations; `PasswordChangeView` is a bare `APIView` that returns 204.

## Goals / Non-Goals

**Goals:**

- Generate a current OpenAPI 3.0 document from the actual views and serializers, with one canonical operation per supported `/api/` route.
- Serve Swagger UI and its assets in the project's normal browser workflow, with a JWT authorization control.
- Keep documentation metadata aligned with account action behavior and collection pagination/search.

**Non-Goals:**

- Change endpoint authorization, business rules, models, or database state.
- Add new business endpoints or treat Swagger access as permission to call protected endpoints.
- Publish the legacy `/timetables/` alias as a second API surface.

## Decisions

### Generate schema with drf-spectacular

Add a compatible pinned `drf-spectacular` release, register `drf_spectacular`, and set DRF's default schema class to `drf_spectacular.openapi.AutoSchema`. Set `SPECTACULAR_SETTINGS` metadata, explicitly use OpenAPI 3.0.3, and serve `SpectacularAPIView` at `/api/schema/` and `SpectacularSwaggerView` at `/api/docs/`, before the `/api/` includes. Make the schema and UI readable without JWT while retaining existing endpoint permissions. Prefer `drf-spectacular-sidecar` assets so the UI works without an external CDN; ensure normal static file handling serves those assets. A hand-maintained OpenAPI file would drift from the serializers and does not satisfy automatic generation.

### Publish canonical paths only

Use a small schema preprocessing hook to remove `/timetables/` alias entries from the generated endpoint list and keep the `/api/` operations. Exclude any wildcard fallback or documentation routes if discovery would otherwise include them. This preserves runtime routing and avoids maintaining a second URL configuration. A separate schema-only URL configuration would duplicate route declarations and need updates whenever API routes change.

### Annotate only where inference is wrong

Let model serializers and router actions provide the base schema. Add targeted `extend_schema` metadata for `RegisterView`'s `UserSerializer` response; `UserViewSet.partial_update`'s `ProfileSerializer` request and `UserSerializer` response; the `role` action's `RoleSerializer` request and `UserSerializer` response; and `PasswordChangeView`'s password request and empty 204 response. Describe relevant 400/401/403/409 outcomes and public operations without claiming that the schema can encode every business validation rule. Check pagination `page` and `size`, search exposure, teacher read-only methods, and JWT bearer security in the generated document; add metadata only for concrete gaps. This keeps the generated schema as the source of truth for ordinary resources.

## Risks / Trade-offs

- [Dependency compatibility] The published `drf-spectacular` support list currently stops at Django 6.0 and DRF 3.17, while this project pins Django 6.1.2 and DRF 3.18.3. Verify installation, Django checks, schema generation, and UI rendering with these exact versions before accepting the integration. Keep project framework versions required by `temp/project_requirements.md` rather than downgrading them to fit a documentation package.
- [Schema drift in custom actions] Default serializer inference can describe a GET representation as a PATCH body or return body. Compare the generated operation schemas against the existing account views and correct those gaps explicitly.
- [Duplicate or noisy paths] The alias and wildcard route can pollute generated paths. Inspect the produced `paths` map and apply the narrow preprocessing filter while leaving runtime routes intact.
- [Public schema exposure] Anyone can see endpoint structure. The schema and UI contain no account data or secrets; actual resource access continues to require JWT and existing role checks.

## Migration Plan

Install the pinned documentation dependencies with the existing Django and DRF pins, configure the generator and UI, and annotate the custom account operations. Run Django checks and the schema generation command with validation, then inspect schema paths, methods, request/response structures, and security declarations. Open `/api/docs/` and `/api/schema/` without a token, then authorize Swagger UI with an access token and confirm a protected request still applies normal permissions. Update the README with the docs URL and token flow. No data migration is needed. Rollback removes the documentation dependencies, settings, URL entries, metadata, and README section; existing API data and routes remain usable.
