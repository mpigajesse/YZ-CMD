from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('article', '0013_article_prix_achat_article_prix_upsell_4'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='article',
            name='prix_unitaire_positif',
        ),
        migrations.AddConstraint(
            model_name='article',
            constraint=models.CheckConstraint(
                check=models.Q(prix_unitaire__gte=0),
                name='prix_unitaire_positif'
            ),
        ),
    ] 