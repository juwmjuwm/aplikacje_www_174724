# The Timetabler

## Timetable API

Install dependencies with `pip install -r requirements.txt`. Copy `.env.example`
to `.env` and replace its placeholders. `DJANGO_SECRET_KEY` is required for
Django and JWT signing. Set `INITIAL_ADMIN_USERNAME` and
`INITIAL_ADMIN_PASSWORD` before initial bootstrap. The `.env` file is ignored
by Git; existing host environment variables take precedence.

Run `python manage.py migrate`, then `python manage.py bootstrap_accounts`, then
`python manage.py runserver`. Run bootstrap after migrations on each deployment
start. It creates the `PLANNER` group and, if none exists, an ADMIN superuser
from the initial credentials. Repeated runs preserve its password and
privileges. Missing credentials when no ADMIN exists, or a configured username
already held by a regular user, cause a clear error.

## Authentication and users

Register a VIEWER with `POST /api/register/` and
`{"username":"alice","email":"alice@example.com","password":"Strong-unique-pass-123"}`.
`email` is optional. Registration validates passwords and rejects privilege
fields. The response contains `id`, `username`, `email`, and `role`, never the
password.

Obtain tokens with `POST /api/token/` and
`{"username":"alice","password":"Strong-unique-pass-123"}`. Refresh access
with `POST /api/token/refresh/` and `{"refresh":"<refresh token>"}`. Send
`Authorization: Bearer <access token>` on protected requests. Missing or invalid
tokens return HTTP 401. Role changes take effect on existing access tokens.

The account holder or ADMIN may `GET` or `PATCH /api/users/{id}/`. PATCH accepts
only `username` and `email`, for example `{"email":"new@example.com"}`.
ADMIN may `GET /api/users/` and `PATCH /api/users/{id}/role/` with
`{"role":"PLANNER"}` or `{"role":"VIEWER"}`. Only ADMIN may
`DELETE /api/users/{id}/`, and only when the target is currently VIEWER. A
PLANNER must be demoted first. Deleting PLANNER or ADMIN returns HTTP 409;
other users receive HTTP 403. Deleted accounts lose access immediately.

## Scheduling access

Authenticated VIEWER, PLANNER, and ADMIN accounts can read scheduling data.
Only PLANNER and ADMIN can create, update, or delete it; VIEWER writes return
HTTP 403. Timetables are shared, so any PLANNER or ADMIN may edit them.

All API paths end in `/` and exchange JSON. Each collection supports `GET` (200,
JSON array) and `POST` (201, created record). Each detail path appends an integer
`id` and supports `GET`, `PUT`, and `PATCH` (200, JSON record), plus `DELETE`
(204, empty body). The `id` field in every response is read-only.

| Collection path | Writable request fields |
| --- | --- |
| `/api/timetables/` | `name`, optional `description` |
| `/api/student-groups/` | `name`, `size` (positive integer) |
| `/api/subjects/` | `name`, optional `description` |
| `/api/teachers/` | `first_name`, `last_name`, optional `academic_title`, optional `email` |
| `/api/rooms/` | `name`, `capacity` (positive integer) |
| `/api/lessons/` | `timetable`, `student_group`, `subject`, `teacher`, `room` (existing record IDs); `weekday` (`MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, or `SUN`); `start_time`, `end_time` (for example, `09:00:00`) |

For example, create a timetable with
`POST /api/timetables/` and `{"name":"Autumn"}`. Create a lesson
with `POST /api/lessons/` and a body such as:

```json
{
  "timetable": 1,
  "student_group": 1,
  "subject": 1,
  "teacher": 1,
  "room": 1,
  "weekday": "MON",
  "start_time": "09:00:00",
  "end_time": "10:00:00"
}
```

Relations are returned as IDs. A missing or nonexistent related ID returns
HTTP 400 with errors keyed by field, such as `{"room":["Invalid pk ..."]}`.
Invalid lesson intervals return an `end_time` error; overlapping room, teacher,
or student group bookings return an error keyed by the conflicting resource.
Unexpected concurrent conflicts caught by the SQLite scheduling trigger return
HTTP 400 with `non_field_errors`.

Missing records and unknown `/api/` paths return HTTP 404 with a JSON `detail`
message. Unsupported methods return HTTP 405 with the method named in `detail`.
Deleting a student group, subject, teacher, or room used by a lesson returns
HTTP 409 with a `detail` message explaining that related lessons prevent
deletion. Deleting a timetable removes its lessons as well.

### Owner removal migration

`Timetable.owner` has been removed from storage and JSON. Clients must stop
sending or expecting `owner`; POST, PUT, and PATCH with that field return HTTP
400. Existing timetable and lesson rows survive migration 0002, but owner IDs
are discarded. Back up the SQLite database before migrating if those IDs are
needed for historical records. Existing clients must obtain a JWT before using
scheduling or user routes.
