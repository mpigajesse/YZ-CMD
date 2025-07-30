import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.models import Article

print("Vérification des images externes (image_url) :\n")
nb_avec_url = 0
nb_sans_url = 0

for art in Article.objects.all():
    if art.image_url:
        print(f"✅ {art.reference} | {art.nom} : image_url = {art.image_url}")
        nb_avec_url += 1
    else:
        print(f"❌ {art.reference} | {art.nom} : PAS D'IMAGE_URL")
        nb_sans_url += 1

print(f"\nTotal avec image_url : {nb_avec_url}")
print(f"Total sans image_url : {nb_sans_url}")
print(f"Total articles : {Article.objects.count()}")