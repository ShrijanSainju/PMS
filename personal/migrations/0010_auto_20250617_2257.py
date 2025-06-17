import uuid
from django.db import migrations, models

def generate_unique_uuids(apps, schema_editor):
    ParkingSession = apps.get_model('personal', 'ParkingSession')
    for session in ParkingSession.objects.all():
        session.session_id = uuid.uuid4()
        session.save()

class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0009_parkingsession_duration'),  # Replace '0009_previous_migration' with your latest migration before 10
    ]

    operations = [
        # Step 1: Add field nullable without unique
        migrations.AddField(
            model_name='parkingsession',
            name='session_id',
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: Fill existing rows with unique UUIDs
        migrations.RunPython(generate_unique_uuids, reverse_code=migrations.RunPython.noop),
        # Step 3: Alter field to unique and not nullable
        migrations.AlterField(
            model_name='parkingsession',
            name='session_id',
            field=models.UUIDField(unique=True, editable=False, null=False),
        ),
    ]
