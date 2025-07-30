from django.core.management.base import BaseCommand
from article.models import Article
from django.db import transaction

class Command(BaseCommand):
    help = 'Corrects Article prices that are zero or negative to a small positive value (0.01).'

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix article prices...")
        
        try:
            with transaction.atomic():
                # Filter for articles with prix_unitaire <= 0
                articles_to_fix = Article.objects.filter(prix_unitaire__lte=0)
                
                fixed_count = 0
                for article in articles_to_fix:
                    original_price = article.prix_unitaire
                    article.prix_unitaire = 0.01  # Set to a small positive value
                    article.save()
                    fixed_count += 1
                    self.stdout.write(f"Fixed Article ID: {article.id}, Ref: {article.reference}, Old Price: {original_price} -> New Price: {article.prix_unitaire}")
                
                self.stdout.write(self.style.SUCCESS(f"Successfully fixed {fixed_count} articles."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            self.stdout.write(self.style.ERROR("Transaction rolled back.")) 