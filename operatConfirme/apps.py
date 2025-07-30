from django.apps import AppConfig


class OperatconfirmeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operatConfirme'
    verbose_name = 'Opérateur de Confirmation'

    # Les signals sont maintenant gérés dans l'application 'parametre'
