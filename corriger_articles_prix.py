import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.models import Article

PRIX_PAR_DEFAUT = 1.0  # À adapter si besoin

articles_pb = Article.objects.filter(prix_unitaire__lte=0)
print(f"Articles avec prix <= 0 : {articles_pb.count()}")

for art in articles_pb:
    print(f"- {art.id} | {art.reference} | {art.nom} | Ancien prix: {art.prix_unitaire}")
    art.prix_unitaire = PRIX_PAR_DEFAUT
    art.save()
    print(f"  -> Corrigé à {PRIX_PAR_DEFAUT} DH")

print("\n✅ Correction terminée. Tous les articles ont maintenant un prix strictement positif.") 