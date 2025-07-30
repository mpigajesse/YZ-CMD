from django.apps import AppConfig


class OperatlogisticConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operatLogistic'
    verbose_name = 'Opérateur Logistique'
    
    # Les signals sont maintenant gérés dans l'application 'parametre'
