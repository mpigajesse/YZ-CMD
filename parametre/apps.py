from django.apps import AppConfig


class ParametreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parametre'
    verbose_name = 'Paramètres'

    def ready(self):
        import parametre.signals
