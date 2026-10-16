from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('timetables', '0001_initial')]

    operations = [migrations.RemoveField(model_name='timetable', name='owner')]
