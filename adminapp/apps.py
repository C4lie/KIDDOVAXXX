from django.apps import AppConfig
from django.db.models.signals import post_migrate


def auto_seed_production_db(sender, **kwargs):
    try:
        from adminapp.models import City
        if City.objects.count() == 0:
            from django.core.management import call_command
            call_command('seed_db')
    except Exception:
        pass


class AdminappConfig(AppConfig):
    name = 'adminapp'

    def ready(self):
        import kiddovax.signals  # noqa
        post_migrate.connect(auto_seed_production_db, sender=self)
