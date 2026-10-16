# Tasks

## 1. Generated schema and browser UI

- [ ] 1.1 Add pinned `drf-spectacular` and sidecar dependencies while retaining Django 6.1.2 and DRF 3.18.3; verify installation and `manage.py check` succeed with the resolved versions.
- [ ] 1.2 Configure OpenAPI 3.0.3 generation, public schema/UI serving, local Swagger assets, and `/api/schema/` plus `/api/docs/` routes; verify unauthenticated GET requests load the schema and a rendered Swagger UI.
- [ ] 1.3 Restrict published schema paths to supported canonical `/api/` operations while preserving runtime `/timetables/` routes; verify the generated `paths` map contains neither alias duplicates nor wildcard fallbacks.
- [ ] 1.4 Document the docs URL, schema URL, token acquisition, and Swagger authorization steps in `README.md`; verify the instructions work against the running project.

## 2. Operation accuracy

- [ ] 2.1 Describe registration, profile PATCH, role PATCH, and password change with their actual request serializers, success responses, and relevant error statuses; verify the generated operation definitions distinguish the bodies and show password change as bodyless HTTP 204.
- [ ] 2.2 Review generated security requirements, supported methods, resource fields, paginated envelopes, and `page`, `size`, and `search` parameters; correct concrete inaccuracies and verify public token/registration operations and protected JWT operations are represented correctly.

## 3. Integration verification

- [ ] 3.1 Run Django checks and schema generation with validation on the pinned dependency set; verify the output is valid OpenAPI 3.0 and address warnings that indicate missing or inaccurate operations.
- [ ] 3.2 Open Swagger UI, obtain an access token, authorize a protected read, and confirm an anonymous protected request still receives the existing authorization response; verify documentation access does not alter API permissions.
