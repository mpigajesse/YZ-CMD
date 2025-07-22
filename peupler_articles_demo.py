import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.models import Article

# Nettoyage complet
Article.objects.all().delete()
print("Tous les articles existants ont été supprimés.")

# Nous allons générer des URLs Lorem Picsum uniques pour chaque article directement dans la boucle

print("Création de 50 articles de chaque type avec image_url Lorem Picsum...")

for i in range(1, 51):
    # Article en liquidation
    Article.objects.create(
        reference=f"LIQ-{i:03d}",
        nom=f"Chaussure Liquidation {i}",
        couleur="Noir",
        pointure=str(40 + (i % 5)),
        prix_unitaire=Decimal('299.99'),
        prix_achat=Decimal('150.00'),
        categorie="HOMME",
        phase='LIQUIDATION',
        qte_disponible=500,
        description=f"Article en liquidation n°{i}, upsell désactivé automatiquement.",
        isUpsell=False,
        actif=True,
        image_url=f"https://picsum.photos/400/400?random={i + 100}", # Décalage pour varier les images
    )

    # Article en test
    Article.objects.create(
        reference=f"TEST-{i:03d}",
        nom=f"Chaussure Test {i}",
        couleur="Blanc",
        pointure=str(37 + (i % 5)),
        prix_unitaire=Decimal('199.99'),
        prix_achat=Decimal('100.00'),
        categorie="FEMME",
        phase='EN_TEST',
        qte_disponible=500,
        description=f"Article en phase de test n°{i}, upsell désactivé automatiquement.",
        isUpsell=False,
        actif=True,
        image_url=f"https://picsum.photos/400/400?random={i + 200}", # Décalage pour varier les images
    )

    # Article en promo
    Article.objects.create(
        reference=f"PROMO-{i:03d}",
        nom=f"Chaussure Promo {i}",
        couleur="Rouge",
        pointure=str(38 + (i % 5)),
        prix_unitaire=Decimal('349.99'),
        prix_achat=Decimal('180.00'),
        categorie="FEMME",
        phase='EN_COURS',
        qte_disponible=500,
        description=f"Article en promotion n°{i} (ajouter la promo via l'admin).",
        isUpsell=False,
        actif=True,
        image_url=f"https://picsum.photos/400/400?random={i + 200}", # Décalage pour varier les images
    )

    # Article upsell avec tous les prix upsell
    Article.objects.create(
        reference=f"UPSELL-{i:03d}",
        nom=f"Chaussure Upsell {i}",
        couleur="Bleu",
        pointure=str(41 + (i % 5)),
        prix_unitaire=Decimal('399.99'),
        prix_achat=Decimal('200.00'),
        categorie="HOMME",
        phase='EN_COURS',
        qte_disponible=500,
        description=f"Article avec tous les prix upsell n°{i}.",
        isUpsell=True,
        prix_upsell_1=Decimal('379.99'),
        prix_upsell_2=Decimal('359.99'),
        prix_upsell_3=Decimal('339.99'),
        prix_upsell_4=Decimal('319.99'),
        actif=True,
        image_url=f"https://picsum.photos/400/400?random={i + 300}", # Décalage pour varier les images
    )

    # Article upsell simple
    Article.objects.create(
        reference=f"UPSELLSIMP-{i:03d}",
        nom=f"Chaussure Upsell Simple {i}",
        couleur="Vert",
        pointure=str(39 + (i % 5)),
        prix_unitaire=Decimal('299.99'),
        prix_achat=Decimal('150.00'),
        categorie="HOMME",
        phase='EN_COURS',
        qte_disponible=500,
        description=f"Article avec un seul prix upsell n°{i}.",
        isUpsell=True,
        prix_upsell_1=Decimal('279.99'),
        actif=True,
        image_url=f"https://picsum.photos/400/400?random={i + 400}", # Décalage pour varier les images
    )

print("✅ 50 articles de chaque type créés avec image_url Lorem Picsum !") 