from django.db import migrations


def backfill_estado(apps, schema_editor):
    Purchase = apps.get_model('purchasing', 'Purchase')
    Purchase.objects.all().update(estado=1)  # 1 = CONFIRMADA


class Migration(migrations.Migration):
    dependencies = [('purchasing', '0002_purchase_estado_suppliercreditnote_tax_amount')]

    operations = [migrations.RunPython(backfill_estado, migrations.RunPython.noop)]
