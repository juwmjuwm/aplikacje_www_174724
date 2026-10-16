import unicodedata

from django.db import migrations


def normalize_existing_accounts(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    db = schema_editor.connection.alias
    rows = list(User.objects.using(db).values_list('pk', 'username', 'first_name', 'last_name'))
    invalid = []
    updates = []

    for pk, username, first_name, last_name in rows:
        canonical = unicodedata.normalize('NFKC', username).casefold()
        if (not username or len(username) > 150 or len(canonical) > 150
                or not all(char.isalpha() or char.isdecimal() or char == '_' for char in username)
                or not all(char.isalpha() or char.isdecimal() or char == '_' for char in canonical)):
            invalid.append(f'id={pk} username={username!r}: unsupported username characters or length')

        normalized = {}
        for field, value in (('first_name', first_name), ('last_name', last_name)):
            if not value:
                continue
            stripped = value.strip()
            capitalized = stripped.capitalize()
            if not stripped or not all(char.isalpha() for char in stripped) or len(capitalized) > 150:
                invalid.append(f'id={pk} {field}={value!r}: use 1-150 Unicode letters')
            elif value != capitalized:
                normalized[field] = capitalized
        if normalized:
            updates.append((pk, normalized))

    if invalid:
        raise RuntimeError(
            'Cannot enforce account formats. Correct the listed account fields '
            'while preserving account IDs and relationships, then rerun migrate. '
            'No accounts were changed.\n' + '\n'.join(invalid)
        )

    for pk, values in updates:
        User.objects.using(db).filter(pk=pk).update(**values)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_alter_user_username')]
    operations = [migrations.RunPython(normalize_existing_accounts, migrations.RunPython.noop)]
