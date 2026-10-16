from django.db import migrations


def drop_legacy_email(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = {column.name for column in connection.introspection.get_table_description(cursor, 'auth_user')}
        if 'email' in columns:
            cursor.execute('ALTER TABLE auth_user DROP COLUMN email')


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]
    operations = [migrations.RunPython(drop_legacy_email)]
