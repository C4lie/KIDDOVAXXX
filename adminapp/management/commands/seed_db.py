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
        else:
            self.stdout.write(self.style.WARNING("initial_data.json not found."))
