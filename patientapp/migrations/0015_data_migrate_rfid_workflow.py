"""Data migration: Set existing patients to ACTIVE, migrate appointment statuses, hash passwords."""
from django.db import migrations


def migrate_existing_data(apps, schema_editor):
    """
    1. Set all existing patients to ACTIVE with must_change_password=False (grandfathered).
    2. Migrate appointment active=2 (old 'Checked-Out/Completed') to active=4 (new COMPLETED).
    3. Migrate appointment active=3 (old 'Cancelled via SMS') to active=5 (new CANCELLED).
    4. Hash all existing plain-text patient passwords.
    """
    Patienttbl = apps.get_model('patientapp', 'Patienttbl')
    Appointmenttbl = apps.get_model('patientapp', 'Appointmenttbl')

    # 1. Grandfather existing patients
    Patienttbl.objects.all().update(account_status='ACTIVE', must_change_password=False)

    # 2. Migrate old completed appointments (active=2 → active=4)
    Appointmenttbl.objects.filter(active=2).update(active=4)

    # 3. Migrate old cancelled appointments (active=3 → active=5)
    Appointmenttbl.objects.filter(active=3).update(active=5)

    # 4. Hash existing plain-text passwords
    from django.contrib.auth.hashers import make_password, identify_hasher
    for patient in Patienttbl.objects.all():
        try:
            identify_hasher(patient.password)
            # Already hashed — skip
        except Exception:
            # Plain text — hash it
            patient.password = make_password(patient.password)
            patient.save(update_fields=['password'])


def reverse_migration(apps, schema_editor):
    """Reverse: set statuses back. Cannot unhash passwords."""
    Patienttbl = apps.get_model('patientapp', 'Patienttbl')
    Appointmenttbl = apps.get_model('patientapp', 'Appointmenttbl')

    # Reverse appointment status
    Appointmenttbl.objects.filter(active=4).update(active=2)
    Appointmenttbl.objects.filter(active=5).update(active=3)

    # Reset account status
    Patienttbl.objects.all().update(account_status='PENDING_HOSPITAL_REGISTRATION', must_change_password=True)


class Migration(migrations.Migration):

    dependencies = [
        ('patientapp', '0014_rfid_workflow_redesign'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_data, reverse_migration),
    ]
