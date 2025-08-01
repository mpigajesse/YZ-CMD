# Generated by Django 5.1.7 on 2025-06-21 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('synchronisation', '0002_synclog_end_time_synclog_execution_details_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='synclog',
            name='duplicate_orders_found',
            field=models.IntegerField(default=0, verbose_name='Doublons détectés et évités'),
        ),
        migrations.AddField(
            model_name='synclog',
            name='existing_orders_skipped',
            field=models.IntegerField(default=0, verbose_name='Commandes existantes inchangées'),
        ),
        migrations.AddField(
            model_name='synclog',
            name='existing_orders_updated',
            field=models.IntegerField(default=0, verbose_name='Commandes existantes mises à jour'),
        ),
        migrations.AddField(
            model_name='synclog',
            name='new_orders_created',
            field=models.IntegerField(default=0, verbose_name='Nouvelles commandes créées'),
        ),
    ]
