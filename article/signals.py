from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps

@receiver(post_migrate)
def create_default_genres(sender, **kwargs):
    # Vérifie que c'est ton app
    if sender.name == 'articles':
        Genre = apps.get_model('articles', 'Genre')
        for nom in ['HOMME', 'FEMME', 'FILLE', 'GARCON']:
            Genre.objects.get_or_create(nom=nom)
