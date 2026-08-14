from django.apps import AppConfig


class AdminappConfig(AppConfig):
    name = 'adminapp'

    def ready(self):
        import kiddovax.signals  # noqa
