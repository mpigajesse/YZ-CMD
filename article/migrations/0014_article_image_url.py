from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('article', '0013_article_prix_achat_article_prix_upsell_4'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='image_url',
            field=models.URLField(blank=True, null=True, help_text="Lien direct vers une image externe (ex: Unsplash)"),
        ),
    ] 