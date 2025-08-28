from django.db import migrations, connection


TARGET_START_ID = 211971


def set_commande_id_sequence(apps, schema_editor):
    Commande = apps.get_model('commande', 'Commande')
    table_name = Commande._meta.db_table

    with connection.cursor() as cursor:
        vendor = connection.vendor

        if vendor == 'sqlite':
            cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = cursor.fetchone()[0] or 0
            desired_next_id = max(TARGET_START_ID, max_id + 1)
            desired_last_used = desired_next_id - 1

            cursor.execute(
                "SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            )
            has_sqlite_sequence = cursor.fetchone()[0] == 1
            if not has_sqlite_sequence:
                return

            cursor.execute(
                "SELECT COUNT(1) FROM sqlite_sequence WHERE name = ?", [table_name]
            )
            exists = cursor.fetchone()[0] == 1
            if exists:
                cursor.execute(
                    "UPDATE sqlite_sequence SET seq = ? WHERE name = ?",
                    [desired_last_used, table_name],
                )
            else:
                cursor.execute(
                    "INSERT INTO sqlite_sequence(name, seq) VALUES(?, ?)",
                    [table_name, desired_last_used],
                )

        elif vendor == 'postgresql':
            cursor.execute(
                "SELECT pg_get_serial_sequence(%s, %s)", [table_name, 'id']
            )
            seq_row = cursor.fetchone()
            if not seq_row or not seq_row[0]:
                return
            sequence_name = seq_row[0]

            cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = cursor.fetchone()[0] or 0
            desired_next_id = max(TARGET_START_ID, max_id + 1)

            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH %s", [desired_next_id])

        else:
            pass


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('commande', '0006_alter_envoi_status'),
    ]

    operations = [
        migrations.RunPython(set_commande_id_sequence, reverse_code=noop_reverse),
    ]


