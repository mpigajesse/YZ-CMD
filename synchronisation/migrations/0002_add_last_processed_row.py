# Generated manually to add last_processed_row field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('synchronisation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlesheetconfig',
            name='last_processed_row',
            field=models.IntegerField(
                default=0,
                verbose_name='Dernière ligne traitée',
                help_text='Numéro de la dernière ligne traitée lors de la synchronisation précédente'
            ),
        ),
    ]
