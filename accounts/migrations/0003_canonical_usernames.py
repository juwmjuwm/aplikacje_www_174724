from django.db import migrations
from django.core.exceptions import ValidationError

from accounts.usernames import validate_username


def canonicalize_usernames(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    rows = list(User.objects.using(schema_editor.connection.alias).values_list('pk', 'username'))
    canonical_names = {}
    conflicts = []
    invalid = []

    for pk, username in rows:
        try:
            canonical = validate_username(username)
        except ValidationError as exc:
            invalid.append(f'id={pk} username={username!r}: {exc}')
            continue
        canonical_names.setdefault(canonical, []).append((pk, username))

    for canonical, accounts in canonical_names.items():
        if len(accounts) > 1:
            members = ', '.join(f'id={pk} username={username!r}' for pk, username in accounts)
            conflicts.append(f'{canonical!r}: {members}')

    if invalid or conflicts:
        details = '\n'.join(
            [f'Invalid username: {item}' for item in invalid]
            + [f'Username collision: {item}' for item in conflicts]
        )
        raise RuntimeError(
            'Cannot canonicalize usernames. Rename the listed accounts to distinct valid '
            f'usernames and rerun migrate. No usernames were changed.\n{details}'
        )

    for canonical, accounts in canonical_names.items():
        pk, username = accounts[0]
        if username != canonical:
            User.objects.using(schema_editor.connection.alias).filter(pk=pk).update(username=canonical)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_drop_legacy_email')]
    operations = [migrations.RunPython(canonicalize_usernames, migrations.RunPython.noop)]
