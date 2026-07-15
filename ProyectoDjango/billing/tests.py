from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase

from shared.validators import validate_only_letters, validate_phone_ec
from .forms import CreditNoteForm
from .models import Brand, Customer, CreditNote, Invoice, InvoiceDetail, Product, ProductGroup
from .services import emit_invoice, recalc_invoice


class ValidatorsTests(TestCase):
    def test_validate_only_letters_accepts_accented_names(self):
        validate_only_letters('José Pérez')  # no debe lanzar

    def test_validate_only_letters_rejects_digits(self):
        with self.assertRaises(ValidationError):
            validate_only_letters('Juan123')

    def test_validate_phone_ec_accepts_ecuadorian_mobile(self):
        validate_phone_ec('0991234567')  # no debe lanzar

    def test_validate_phone_ec_rejects_letters(self):
        with self.assertRaises(ValidationError):
            validate_phone_ec('abcdefghij')


class InvoiceElectronicEmailTests(TestCase):
    """Verifica que emit_invoice() envíe la factura electrónica por correo."""

    def setUp(self):
        brand = Brand.objects.create(name='MarcaTest')
        group = ProductGroup.objects.create(name='GrupoTest')
        self.product = Product.objects.create(
            name='ProductoTest', brand=brand, group=group,
            unit_price=Decimal('10.00'), stock=5,
        )
        self.user = User.objects.create_user('vendedor_test', password='x')

    def _crear_factura_emitida(self, customer):
        invoice = Invoice.objects.create(customer=customer, estado=Invoice.BORRADOR)
        InvoiceDetail.objects.create(
            invoice=invoice, product=self.product, quantity=2, unit_price=self.product.unit_price,
        )
        recalc_invoice(invoice)
        emit_invoice(invoice, self.user, tipo_pago=Invoice.CONTADO)
        return invoice

    def test_emit_invoice_sends_email_with_pdf_attached(self):
        customer = Customer.objects.create(
            dni='0912345678', first_name='Juan', last_name='Perez', email='cliente@example.com',
        )
        self._crear_factura_emitida(customer)

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn(customer.email, sent.to)
        self.assertEqual(len(sent.attachments), 1)
        filename, content, mimetype = sent.attachments[0]
        self.assertEqual(mimetype, 'application/pdf')
        self.assertTrue(content.startswith(b'%PDF'))

    def test_emit_invoice_skips_email_silently_without_customer_email(self):
        customer_sin_email = Customer.objects.create(dni='0923456789', first_name='Ana', last_name='Ruiz')
        self._crear_factura_emitida(customer_sin_email)

        self.assertEqual(len(mail.outbox), 0)


class CreditNoteValidationTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name='MarcaTest2')
        group = ProductGroup.objects.create(name='GrupoTest2')
        self.product = Product.objects.create(
            name='ProductoTest2', brand=brand, group=group,
            unit_price=Decimal('50.00'), stock=10,
        )
        self.customer = Customer.objects.create(
            dni='0934567890', first_name='Luis', last_name='Cedeno', email='luis@example.com',
        )
        self.user = User.objects.create_user('vendedor_test2', password='x')

        self.invoice = Invoice.objects.create(customer=self.customer, estado=Invoice.BORRADOR)
        InvoiceDetail.objects.create(
            invoice=self.invoice, product=self.product, quantity=1, unit_price=self.product.unit_price,
        )
        recalc_invoice(self.invoice)
        emit_invoice(self.invoice, self.user, tipo_pago=Invoice.CONTADO)

    def test_rejects_amount_over_available_balance(self):
        form = CreditNoteForm(data={
            'tipo':   CreditNote.TIPO_PARCIAL,
            'amount': self.invoice.total + Decimal('100'),
            'reason': 'Producto defectuoso',
        }, invoice=self.invoice)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_rejects_reason_too_short(self):
        form = CreditNoteForm(data={
            'tipo':   CreditNote.TIPO_TOTAL,
            'amount': self.invoice.total,
            'reason': 'x',
        }, invoice=self.invoice)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)

    def test_accepts_valid_credit_note_within_balance(self):
        form = CreditNoteForm(data={
            'tipo':   CreditNote.TIPO_TOTAL,
            'amount': self.invoice.total,
            'reason': 'Devolución por producto defectuoso',
        }, invoice=self.invoice)
        self.assertTrue(form.is_valid(), form.errors)
