from django.apps import AppConfig


class CommandeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commande'

    def ready(self):
        # Enregistrer les signaux (inclut l'initialisation des états par défaut)
        from . import signals  # noqa: F401
