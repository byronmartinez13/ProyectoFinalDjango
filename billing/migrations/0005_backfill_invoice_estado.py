from django.db import migrations


def set_existing_invoices_emitida(apps, schema_editor):
    Invoice = apps.get_model('billing', 'Invoice')
    Invoice.objects.filter(estado=0).update(estado=1)


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_invoice_estado_creditnote'),
    ]

    operations = [
        migrations.RunPython(
            set_existing_invoices_emitida,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
