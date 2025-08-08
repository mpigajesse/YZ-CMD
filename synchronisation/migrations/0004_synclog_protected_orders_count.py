# Generated manually for adding protected_orders_count field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('synchronisation', '0003_synclog_duplicate_orders_found_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='synclog',
            name='protected_orders_count',
            field=models.IntegerField(default=0, verbose_name='Commandes protégées contre la régression d\'état'),
        ),
    ] 