from django.apps import AppConfig

class FunatiappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'funATIAPP'

    def ready(self):
        import funATIAPP.signals

