# Generated by Django 5.1.7 on 2025-06-16 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commande', '0003_alter_enumetatcmd_options'),
        ('parametre', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='ville_init',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='commande',
            name='ville',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commandes', to='parametre.ville'),
        ),
    ]
