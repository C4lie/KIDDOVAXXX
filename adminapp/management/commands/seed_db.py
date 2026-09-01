import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from hospitalapp.models import Hospitaltbl

class Command(BaseCommand):
    help = "Seed initial production data from initial_data.json fixture"

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'initial_data.json')
        if os.path.exists(fixture_path):
            self.stdout.write(self.style.SUCCESS("Loading complete database snapshot from initial_data.json..."))
            try:
                call_command('loaddata', fixture_path)
                self.stdout.write(self.style.SUCCESS(f"Successfully loaded {Hospitaltbl.objects.count()} hospitals and all database records into production!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading fixture: {e}"))
        # Deduplicate duplicate Area records in the database
        try:
            from adminapp.models import Area
            from hospitalapp.models import Receptionisttbl
            from patientapp.models import Patienttbl
            seen = set()
            deleted_count = 0
            for area in Area.objects.all().order_by('id'):
                key = (area.areaName.strip().lower(), area.cityId_id)
                if key in seen:
                    orig_area = Area.objects.filter(areaName__iexact=area.areaName.strip(), cityId_id=area.cityId_id).exclude(id=area.id).first()
                    if orig_area:
                        Hospitaltbl.objects.filter(areaId=area).update(areaId=orig_area)
                        Receptionisttbl.objects.filter(areaId=area).update(areaId=orig_area)
                        Patienttbl.objects.filter(areaId=area).update(areaId=orig_area)
                    area.delete()
                    deleted_count += 1
                else:
                    seen.add(key)
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Deduplicated {deleted_count} duplicate Area records from production database."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Area deduplication notice: {e}"))
