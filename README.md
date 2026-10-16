# The Timetabler

## Timetable API

Install dependencies with `pip install -r requirements.txt`. Copy `.env.example`
to `.env` and replace its placeholders. `DJANGO_SECRET_KEY` is required for
Django and JWT signing. Set `INITIAL_ADMIN_USERNAME` and
`INITIAL_ADMIN_PASSWORD` before initial bootstrap. The `.env` file is ignored
by Git; existing host environment variables take precedence.

For a fresh database, run `python manage.py migrate`, then `python manage.py bootstrap_accounts`, then
`python manage.py runserver`. Run bootstrap after migrations on each deployment
start. It creates the `PLANNER` and `TEACHER` groups and, if none exists, an ADMIN superuser
from the initial credentials. Repeated runs preserve its password and
privileges. Missing credentials when no ADMIN exists, or a configured username
already held by a regular user, cause a clear error.

## Authentication and users

Register a VIEWER with `POST /api/register/` and
`{"username":"alice","password":"Strong-unique-pass-123"}`.
Registration validates passwords and rejects email and privilege
fields. The response contains `id`, `username`, `role`, and `roles`,
never the password. A new VIEWER has `"role":"VIEWER"` and
`"roles":["VIEWER"]`.

Obtain tokens with `POST /api/token/` and
`{"username":"alice","password":"Strong-unique-pass-123"}`. Refresh access
with `POST /api/token/refresh/` and `{"refresh":"<refresh token>"}`. Send
`Authorization: Bearer <access token>` on protected requests. Missing or invalid
tokens return HTTP 401. Role changes take effect on existing access tokens.

The account holder or ADMIN may `GET` or `PATCH /api/users/{id}/`. PATCH accepts
only `username`, for example `{"username":"alice2"}`. Email, password, and
privilege fields return HTTP 400. Account responses never include passwords.
To change your own password, send `POST /api/users/me/password/` with
`{"current_password":"Strong-unique-pass-123","new_password":"Another-strong-pass-456"}`
and a valid access token. The current password must match; the new password
must differ and pass the registration password policy. Success is HTTP 204 with
an empty body. Missing, invalid, or extra fields return HTTP 400; missing
authentication returns HTTP 401. Obtain new tokens using the new password.
ADMIN may `GET /api/users/` and `PATCH /api/users/{id}/role/` with
`{"roles":["PLANNER","TEACHER"]}`, `{"roles":["TEACHER"]}`,
`{"roles":["PLANNER"]}`, or `{"roles":[]}`. The array is the complete
membership set; an empty array sets VIEWER. It cannot contain VIEWER, ADMIN,
duplicates, or unknown values. Send exactly one of `roles` or the legacy
`role` field. Responses keep `role` for compatibility and include the complete
`roles` array in ADMIN, PLANNER, TEACHER order. For a combined account,
`"role":"PLANNER"` and `"roles":["PLANNER","TEACHER"]`.
The legacy single-role requests are `{"role":"PLANNER"}`,
`{"role":"TEACHER"}`, or `{"role":"VIEWER"}`.
Promote an existing VIEWER with `{"role":"TEACHER"}`. An unassigned TEACHER
may be demoted with `{"role":"VIEWER"}`. Switching directly between TEACHER
and PLANNER using the legacy `role` field returns HTTP 409; transition through
VIEWER or use `roles` to set the complete membership set. Removing TEACHER from
an assigned user, including one retaining PLANNER, returns HTTP 409 with
`{"detail":"Reassign or delete this teacher's lessons before removing TEACHER."}`.
Removing only PLANNER from an assigned combined-role teacher succeeds.
The same guard applies to Django Admin group editing. Only ADMIN may
`DELETE /api/users/{id}/`, and only when the regular target has neither
membership. A PLANNER, TEACHER, or combined-role user must first have their
memberships removed. Deleting PLANNER, TEACHER, combined-role, or ADMIN accounts returns HTTP 409;
other users receive HTTP 403. Deleted accounts lose access immediately.

## Scheduling access

Authenticated VIEWER, TEACHER, PLANNER, combined-role, and ADMIN accounts can
read scheduling data. PLANNER membership and ADMIN status allow create, update,
and delete, including when the PLANNER also teaches. VIEWER and TEACHER-only
writes return HTTP 403. Removing PLANNER immediately removes write access from
existing tokens. Timetables are shared, so any PLANNER or ADMIN may edit them.

All API paths end in `/` and exchange JSON. Except for the teacher directory, each collection supports `GET` (200,
JSON array) and `POST` (201, created record). Each detail path appends an integer
`id` and supports `GET`, `PUT`, and `PATCH` (200, JSON record), plus `DELETE`
(204, empty body). The `id` field in every response is read-only.

| Collection path | Writable request fields |
| --- | --- |
| `/api/timetables/` | `name`, optional `description` |
| `/api/student-groups/` | `name`, `size` (positive integer) |
| `/api/subjects/` | `name`, optional `description` |
| `/api/teachers/` | Read-only directory of every TEACHER group member, including PLANNER and ADMIN teachers; no writable fields |
| `/api/rooms/` | `name`, `capacity` (positive integer) |
| `/api/lessons/` | `timetable`, `student_group`, `subject`, `room` (existing record IDs), `teacher` (TEACHER user ID); `weekday` (`MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, or `SUN`); `start_time`, `end_time` (for example, `09:00:00`) |

`GET /api/teachers/` returns users such as
`[{"id":7,"username":"alice","role":"PLANNER","roles":["PLANNER","TEACHER"]}]`.
`GET /api/teachers/7/` returns the same object. An ADMIN teacher has
`"role":"ADMIN"` and `"roles":["ADMIN","TEACHER"]`. Users without TEACHER
membership are omitted and return HTTP 404 at the detail path. Teacher POST, PUT, PATCH, and DELETE return
HTTP 405. Assign roles through the user role endpoint.

For example, create a timetable with
`POST /api/timetables/` and `{"name":"Autumn"}`. Create a lesson
with `POST /api/lessons/` and a body such as:

```json
{
  "timetable": 1,
  "student_group": 1,
  "subject": 1,
  "teacher": 7,
  "room": 1,
  "weekday": "MON",
  "start_time": "09:00:00",
  "end_time": "10:00:00"
}
```

Relations, including `teacher`, are returned as IDs. A missing, nonexistent, or
user ID without TEACHER membership in `teacher` returns HTTP 400 with a `teacher`
field error. A PLANNER or ADMIN with TEACHER membership is eligible.
Other missing or nonexistent related IDs return
HTTP 400 with errors keyed by field, such as `{"room":["Invalid pk ..."]}`.
Invalid lesson intervals return an `end_time` error; overlapping room, teacher,
or student group bookings return an error keyed by the conflicting resource.
Unexpected concurrent conflicts caught by the SQLite scheduling trigger return
HTTP 400 with `non_field_errors`.

Missing records and unknown `/api/` paths return HTTP 404 with a JSON `detail`
message. Unsupported methods return HTTP 405 with the method named in `detail`.
Deleting a student group, subject, or room used by a lesson returns
HTTP 409 with a `detail` message explaining that related lessons prevent
deletion. Deleting a timetable removes its lessons as well.

### Owner removal migration

`Timetable.owner` has been removed from storage and JSON. Clients must stop
sending or expecting `owner`; POST, PUT, and PATCH with that field return HTTP
400. Existing timetable and lesson rows survive migration 0002, but owner IDs
are discarded. Back up the SQLite database before migrating if those IDs are
needed for historical records. Existing clients must obtain a JWT before using
scheduling or user routes.

### Teacher replacement migration

Migration 0003 **discards every row in `timetables_teacher` and
`timetables_lesson`** and recreates the lesson table with `teacher_id` pointing
to the configured User table. User accounts, timetables, student groups,
subjects, and rooms are unaffected. Back up the SQLite database before
running `python manage.py migrate` if old teacher or lesson data might be
needed. Run `python manage.py bootstrap_accounts` afterward to create the
TEACHER group. To roll back, restore the database backup together with the
pre-migration application code; reversing the migration cannot recover the
discarded rows. Existing clients must use TEACHER user IDs in lesson payloads.

### Email-free user migration

Fresh databases need only `python manage.py migrate` followed by
`python manage.py bootstrap_accounts`. The active user table is `auth_user`,
without an email column. Registration and profile requests containing email
return HTTP 400, and account and teacher responses omit it.

For an existing SQLite database already migrated through `timetables.0003`,
stop all writers. With the new code and environment loaded, run
`python manage.py prepare_user_migration --backup path/to/backup.sqlite3`
before `python manage.py migrate`. The command checks the expected legacy
tables, columns, migration history, and foreign keys, creates a new backup,
and records the compatible custom user initial migration. It is safe to rerun
after that migration has been recorded. Run `python manage.py migrate`, then
`python manage.py bootstrap_accounts`, and restart the application. Existing
account IDs, password hashes, roles, permissions, and lesson references remain;
stored email values are discarded. To roll back, restore the backup together
with the previous application code. Reversing the email removal migration is
unsupported.
