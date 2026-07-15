from django.db import migrations, models


def backfill_saldo(apps, schema_editor):
    Invoice = apps.get_model('billing', 'Invoice')
    EMITIDA = 1
    for invoice in Invoice.objects.filter(estado=EMITIDA):
        invoice.saldo = invoice.total
        invoice.estado_cobro = 'PAGADA' if invoice.total <= 0 else 'PENDIENTE'
        invoice.save(update_fields=['saldo', 'estado_cobro'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0009_customer_user_invoice_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='saldo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Saldo pendiente de cobro'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='estado_cobro',
            field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('PAGADA', 'Pagada')], default='PENDIENTE', max_length=10, verbose_name='Estado de cobro'),
        ),
        migrations.RunPython(backfill_saldo, noop_reverse),
    ]
