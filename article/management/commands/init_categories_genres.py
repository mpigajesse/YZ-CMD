from django.core.management.base import BaseCommand
from article.models import Categorie, Genre


class Command(BaseCommand):
    help = 'Initialise les catégories et genres avec des données par défaut'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation des catégories...')
        
        # Créer les catégories
        categories_data = [
            'SANDALES',
            'SABOT', 
            'CHAUSSURES',
            'ESPARILLE',
            'BASKET',
            'MULES',
            'PACK_SAC',
            'BOTTE',
            'ESCARPINS',
        ]
        
        for cat_nom in categories_data:
            categorie, created = Categorie.objects.get_or_create(
                nom=cat_nom,
                defaults={
                    'description': f'Catégorie {cat_nom.lower()}',
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Catégorie "{cat_nom}" créée')
            else:
                self.stdout.write(f'  - Catégorie "{cat_nom}" existe déjà')
        
        self.stdout.write('Initialisation des genres...')
        
        # Créer les genres
        genres_data = [
            'HOMME',
            'FEMME',
            'FILLE',
            'GARCON',
        ]
        
        for genre_nom in genres_data:
            genre, created = Genre.objects.get_or_create(
                nom=genre_nom,
                defaults={
                    'description': f'Genre {genre_nom.lower()}',
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Genre "{genre_nom}" créé')
            else:
                self.stdout.write(f'  - Genre "{genre_nom}" existe déjà')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Initialisation terminée ! '
                f'{Categorie.objects.count()} catégories et {Genre.objects.count()} genres disponibles.'
            )
        )
