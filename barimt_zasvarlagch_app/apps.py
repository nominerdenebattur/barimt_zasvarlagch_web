from django.apps import AppConfig

class BarimtZasvarlagchAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'barimt_zasvarlagch_app'

    def ready(self):
        import barimt_zasvarlagch_app.signals
