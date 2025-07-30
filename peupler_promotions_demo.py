import os
import django
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.models import Article, Promotion

# Nettoyage des promotions existantes (optionnel)
Promotion.objects.all().delete()
print("Toutes les promotions existantes ont été supprimées.")

# Sélectionner les articles éligibles (EN_COURS, actifs, sans promo active)
now = timezone.now()
articles_eligibles = Article.objects.filter(
    phase='EN_COURS',
    actif=True
).exclude(
    promotions__active=True,
    promotions__date_debut__lte=now,
    promotions__date_fin__gte=now
).distinct()

print(f"{articles_eligibles.count()} articles éligibles trouvés.")

# Paramètres de génération
NB_PROMOS = 5
ARTICLES_PAR_PROMO = max(1, articles_eligibles.count() // NB_PROMOS)

for i in range(NB_PROMOS):
    articles_promo = list(articles_eligibles[i*ARTICLES_PAR_PROMO:(i+1)*ARTICLES_PAR_PROMO])
    if not articles_promo:
        continue

    nom_promo = f"Promo Démo {i+1}"
    description = f"Promotion automatique de démonstration n°{i+1}."
    pourcentage = random.choice([10, 15, 20, 25, 30])
    date_debut = now - timedelta(days=random.randint(0, 2))
    date_fin = now + timedelta(days=random.randint(3, 10))
    promo = Promotion.objects.create(
        nom=nom_promo,
        description=description,
        pourcentage_reduction=Decimal(pourcentage),
        date_debut=date_debut,
        date_fin=date_fin,
        active=True
    )
    promo.articles.set(articles_promo)
    promo.save()
    print(f"Promotion '{nom_promo}' créée avec {len(articles_promo)} articles et {pourcentage}% de réduction.")

print("✅ Promotions de démonstration créées avec succès !")
