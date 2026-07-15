# Evaluación: próximo CRUD para TecnoStock

Puesto en modo profesor: si tuviera que tomarte un CRUD nuevo como evaluación sobre
este proyecto, no te pediría algo desconectado del dominio (like "gestiona una
biblioteca"). Te pediría algo que **complete un hueco real de TecnoStock** y que se
pueda evaluar con la misma vara que usaste en Facturas/Compras: modelo con estados,
master-detail, permisos por rol, búsqueda + exportación, y que no rompa nada existente.

Esto documenta: (1) los huecos que encontré y candidatos de CRUD para cada uno,
(2) cuál elegiría yo como examen y por qué, (3) el diseño del modelo, y (4) una
checklist de implementación que reutiliza al máximo lo que el proyecto ya tiene,
para que lo puedas resolver rápido bajo presión de examen.

---

## 1. Huecos reales del proyecto (candidatos)

| # | Módulo propuesto | Qué resuelve | Complejidad | Por qué es un buen examen |
|---|---|---|---|---|
| 1 | **Devoluciones de Cliente (RMA)** | Hoy `CreditNote` solo ajusta el monto de la factura — **no revierte stock**. No existe un flujo real de "el cliente devuelve el producto físico". | Media-alta | Usa TODOS los patrones del proyecto a la vez: estados, `StockMovement`, transacciones, permisos. Es el más completo. |
| 2 | **Garantías de producto** | Ninguna factura registra vigencia de garantía ni reclamos post-venta. | Media | Buen master-detail (`InvoiceDetail` → `Garantia`), estado (Vigente/Reclamada/Vencida/Rechazada). |
| 3 | **Cupones / Descuentos** | El carrito (`store`) no soporta códigos promocionales; el total siempre es precio de lista. | Baja-media | CRUD chico y autocontenido, ideal si el examen es corto (2-3h). Pone a prueba validaciones (vigencia, límite de usos). |
| 4 | **Direcciones de envío del Cliente** | `Customer.address` es un solo campo de texto; no hay direcciones múltiples ni "dirección de entrega" por pedido. | Baja | FK simple `Customer → ShippingAddress` (1-a-muchos). Bueno para medir manejo de permisos Cliente-vs-Administrador sobre el mismo modelo. |
| 5 | **Ticket de soporte al cliente** | No hay canal para que un `Cliente` reporte un problema con su pedido; hoy solo existe el correo. | Media | Buen ejemplo de estado + dos roles interactuando (Cliente crea, Vendedor/Administrador responde y cierra). |
| 6 | **Bitácora de auditoría persistida** | `shared/decorators.py::audit_action` ya registra acciones, pero **solo en el log de consola**, no en una tabla consultable. | Baja | Casi no requiere diseño nuevo — es "mover" un patrón que ya existe a un modelo real. Bueno para medir si entiendes lo que ya hay antes de escribir código nuevo. |
| 7 | **Reseñas de producto** | El catálogo (`store/catalog.html`) no tiene calificación ni comentarios de clientes. | Baja | CRUD simple, pero necesita una regla de negocio interesante: solo puede reseñar quien compró el producto (join contra `InvoiceDetail`). |
| 8 | **Configuración general del sistema** | No hay un lugar único para IVA por defecto, datos de la empresa (RUC emisor), moneda — hoy `tax_rate` vive hardcodeado por producto y el RUC del emisor vive en el `.env` del microservicio de facturación. | Baja | Modelo "singleton" (una sola fila) — patrón distinto a todo lo demás, bueno para ver si sabes salir del molde. |

---

## 2. Mi elección: **Devoluciones de Cliente (RMA)**

Si solo pudiera tomar una, sería esta. Motivos como evaluador:

- **Toca CADA capa que ya construiste**: modelo con estado tipo `Invoice`/`Purchase`,
  detalle línea por línea tipo `InvoiceDetail`, movimiento de stock tipo
  `StockMovement`, transacción atómica tipo `emit_invoice()`, permisos nativos tipo
  `export_pdf`, rol tipo `Vendedor`/`Administrador`.
- **Es un hueco real y visible**: hoy si anulas una factura completa se revierte el
  stock (`invoice_cancel`), pero si un cliente devuelve *un solo producto* de una
  compra ya facturada, no tienes cómo registrarlo sin anular toda la factura.
- **Tiene una regla de negocio no trivial** (a diferencia de un CRUD plano): no
  puedes devolver más cantidad de la que se compró, y el stock solo se repone si el
  producto vuelve en buen estado.

### Por qué NO elegiría "Cupones" o "Direcciones" como único examen
Son CRUDs más simples — sirven para un examen corto de 2 horas, pero no exigen
demostrar que sabes coordinar transacciones + inventario + roles a la vez. Los dejo
como plan B/C en la tabla de arriba si el tiempo del examen es limitado.

---

## 3. Diseño del modelo (`ReturnRequest` / `Devolución`)

Ubicación sugerida: nueva app `returns/` (sigue el mismo patrón de apps chicas y
enfocadas que ya usás: `creditoventa`, `pagos`, `inventory`).

```python
# returns/models.py
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models, transaction
from billing.models import Invoice, InvoiceDetail, Product
from shared.money import round_money


class ReturnRequest(models.Model):
    """Devolución de uno o más productos de una factura ya emitida."""
    SOLICITADA = 'solicitada'
    APROBADA   = 'aprobada'
    RECHAZADA  = 'rechazada'
    COMPLETADA = 'completada'   # stock repuesto
    ESTADO_CHOICES = [
        (SOLICITADA, 'Solicitada'),
        (APROBADA,   'Aprobada'),
        (RECHAZADA,  'Rechazada'),
        (COMPLETADA, 'Completada'),
    ]

    invoice     = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='devoluciones')
    fecha       = models.DateField(auto_now_add=True)
    motivo      = models.TextField(verbose_name='Motivo de la devolución')
    estado      = models.CharField(max_length=12, choices=ESTADO_CHOICES, default=SOLICITADA)
    is_active   = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        ordering             = ['-fecha', '-id']
        permissions = [
            ('export_returnrequest_pdf', 'Can export ReturnRequest PDF'),
            ('export_returnrequest_excel', 'Can export ReturnRequest Excel'),
        ]

    @property
    def can_review(self):    return self.estado == self.SOLICITADA
    @property
    def can_complete(self):  return self.estado == self.APROBADA


class ReturnDetail(models.Model):
    """Línea de devolución: qué producto y cuánta cantidad."""
    devolucion = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='detalles')
    invoice_detail = models.ForeignKey(InvoiceDetail, on_delete=models.PROTECT, related_name='devoluciones')
    quantity   = models.IntegerField(validators=[MinValueValidator(1)])

    def clean(self):
        # Regla de negocio: no se puede devolver más de lo vendido en esa línea.
        ya_devuelto = ReturnDetail.objects.filter(
            invoice_detail=self.invoice_detail
        ).exclude(pk=self.pk).aggregate(t=models.Sum('quantity'))['t'] or 0
        disponible = self.invoice_detail.quantity - ya_devuelto
        if self.quantity > disponible:
            from django.core.exceptions import ValidationError
            raise ValidationError(f'Solo puedes devolver hasta {disponible} unidades de este producto.')
```

**Campos y decisiones deliberadamente calcadas de patrones existentes:**
- `estado` con choices + `can_review`/`can_complete` → copiado 1:1 del patrón
  `Invoice.can_edit` / `Invoice.can_confirm`.
- `permissions` en `Meta` → mismo patrón que usamos para `export_pdf` en 6 modelos
  distintos la sesión pasada.
- `ReturnDetail.clean()` valida contra la cantidad ya vendida → mismo espíritu que
  `check_stock()` en `billing/services.py`.

---

## 4. Checklist de implementación — reutilizando lo que ya existe

Este es el orden en el que yo lo resolvería en un examen, apoyándome en piezas que
**ya están escritas** en el proyecto:

1. **App nueva**: `python manage.py startapp returns`, agregarla a `INSTALLED_APPS`
   en `config/settings.py` (junto a `creditoventa`, `pagos`).

2. **Modelo + migraciones**: pegar el diseño de arriba, `makemigrations returns`,
   `migrate returns`.

3. **Lógica de aprobación (reponer stock)** — copiar el patrón exacto de
   `billing/services.py::emit_invoice()` (descuenta stock con `F()` + registra
   `StockMovement` dentro de un `transaction.atomic()`), pero en reversa:

   ```python
   # returns/services.py
   from django.db import transaction
   from django.db.models import F
   from billing.models import Product
   from inventory.models import StockMovement

   @transaction.atomic
   def completar_devolucion(devolucion, user):
       for detalle in devolucion.detalles.select_related('invoice_detail__product'):
           product = detalle.invoice_detail.product
           Product.objects.filter(pk=product.pk).update(stock=F('stock') + detalle.quantity)
           StockMovement.objects.create(
               product=product, quantity=detalle.quantity,
               movement_type=StockMovement.DEVOLUCION_VENTA,  # ya existe, no crear uno nuevo
               user=user, invoice=devolucion.invoice,
           )
       devolucion.estado = ReturnRequest.COMPLETADA
       devolucion.save()
   ```
   `StockMovement.DEVOLUCION_VENTA` **ya existe** (lo usa `invoice_cancel`) — no
   necesitas crear un tipo de movimiento nuevo.

4. **Formset maestro-detalle**: copiar `InvoiceDetailFormSet` de `billing/forms.py`
   (o `PurchaseDetailFormSet` de `purchasing/forms.py`) cambiando el modelo. Esa es
   la parte que más tiempo ahorra: el patrón de formset inline ya está resuelto.

5. **Vistas**: mismo esqueleto que `creditoventa/views.py` (que ya es un CRUD de
   "algo que cuelga de una Invoice"):
   - `ReturnListView` → `LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView`
     (te da búsqueda + exportar PDF/Excel gratis, cero código nuevo).
   - `return_create(request, invoice_pk)` función, igual que `cobro_create`.
   - `return_review(request, pk)` (aprobar/rechazar) — copia el patrón de
     `invoice_confirm` (POST con un choice, cambia estado).

6. **Permisos**: agrega `view_returnrequest`, `add_returnrequest`, etc. (Django los
   crea solos con la migración) **y** los dos custom de exportación de arriba a
   `security/management/commands/setup_roles.py` → dale a `Vendedor` los de
   `add`/`view`, a `Administrador` ya le llegan con `'__all__'`. **No olvides
   re-ejecutar `python manage.py setup_roles`** después de migrar — si no, el
   Administrador no va a tener los permisos nuevos hasta que lo corras (nos pasó
   dos veces en esta sesión).

7. **Templates**: `base.html` ya tiene el patrón de modal `showDetail()` +
   `data-dm-edit-url` condicional a permiso — cópialo tal cual desde
   `creditoventa/templates/creditoventa/factura_list.html` en vez de inventar HTML
   nuevo. Para los botones de exportar, incluye
   `billing/templates/billing/_export_buttons.html` con
   `pdf_perm='returns.export_returnrequest_pdf'` (el partial ya es reusable desde
   cualquier app, no solo `billing`).

8. **Roles/permisos por rol**: no toques nada en `security/` — la pantalla de
   "Permisos por Rol" ya lista *cualquier* permiso del sistema automáticamente.

9. **Notificación al cliente (opcional, para nota extra)**: reutiliza
   `shared/emails.py` como plantilla — copia `send_invoice_email()` y adapta el
   texto ("Tu devolución fue aprobada"). Mismo criterio de *fail-silent* con
   `try/except` + `logger.exception(...)`.

---

## 5. Piezas reutilizables del proyecto (referencia rápida)

| Pieza | Dónde vive | Para qué sirve |
|---|---|---|
| `SearchExportMixin` | `shared/mixins.py` | Búsqueda por querystring + exportar PDF/Excel automático en cualquier `ListView` nueva — solo declaras `search_fields`, `export_fields`, `export_filename`, `export_pdf_perm`, `export_excel_perm`. |
| `GroupRequiredMixin` / `AdminOnlyMixin` / `ClienteRequiredMixin` | `shared/mixins.py` | Restringir una CBV por rol sin escribir `dispatch()` a mano. |
| `roles_required(*roles)` | `shared/decorators.py` | Lo mismo pero para vistas de función. |
| `user_has_role(user, *roles)` | `shared/decorators.py` | Chequeo puntual de rol *dentro* de una vista (no bloquea toda la vista, solo un bloque de código). |
| `audit_action('NOMBRE')` | `shared/decorators.py` | Logging automático de quién hizo qué — decorá tu vista de creación/aprobación. |
| `round_money()` | `shared/money.py` | Redondeo consistente de montos — úsalo en cualquier cálculo financiero nuevo. |
| `validate_cedula_ec` / `validate_phone_ec` / `validate_only_letters` | `shared/validators.py` | Validadores ya hechos para campos ecuatorianos (cédula/RUC, teléfono, nombres). |
| `_export_buttons.html` | `billing/templates/billing/` | Partial reusable de botones Exportar PDF/Excel — recibe `pdf_perm`/`excel_perm` por `{% include ... with %}`. |
| `showDetail()` + `data-dm-*` | `billing/templates/billing/base.html` | Modal de "Ver detalle" sin crear una página nueva — solo agregas atributos `data-dm-*` a un botón. |
| Patrón `emit_invoice()` (F() + StockMovement + `transaction.atomic()`) | `billing/services.py` | Plantilla para cualquier operación que afecte stock de forma auditable. |
| Patrón `registrar_cobro()` (`select_for_update()` + recálculo desde cero) | `creditoventa/models.py` | Plantilla para cualquier "abono progresivo" sobre un documento (evita que el saldo se desincronice). |
| `InvoiceDetailFormSet` / `PurchaseDetailFormSet` | `billing/forms.py`, `purchasing/forms.py` | Plantilla de formset maestro-detalle (cabecera + líneas) — la parte que más cuesta armar desde cero. |
| `setup_roles` command | `security/management/commands/setup_roles.py` | Único lugar donde se asignan permisos a roles por código — **actualízalo y re-ejecútalo** cada vez que agregues un modelo con permisos nuevos, o el Administrador no los va a tener. |
| Permisos custom `Meta.permissions` | cualquier `models.py` | Patrón para acciones que no son CRUD estándar (exportar, aprobar, anular) — se registran solos en la pantalla de Permisos por Rol sin tocar `security/`. |

---

## 6. Notas rápidas para los otros candidatos (si el examen es más corto)

- **Cupones**: modelo único `Coupon(code, discount_pct, valid_from, valid_to, max_uses, times_used, is_active)`.
  Reutiliza `SearchExportMixin` para el listado y `validate_only_letters`-style
  validator custom para el código. No necesita `StockMovement` ni formset.
- **Direcciones de envío**: FK simple a `Customer`, reutiliza el mismo patrón de
  `CustomerProfile` (OneToOne) pero como `ForeignKey` (uno a muchos) + el modal
  `showDetail()` de `customer_list.html` como plantilla de UI.
- **Bitácora persistida**: crea `AuditLog(user, action, path, timestamp)` y modifica
  `audit_action()` en `shared/decorators.py` para que además de `logger.info(...)`
  haga `AuditLog.objects.create(...)`. Es el que menos diseño nuevo requiere.
- **Garantías**: FK a `InvoiceDetail` (no a `Product`, para saber *cuál* venta
  específica generó la garantía), estado tipo `Invoice`, y fecha de vencimiento
  calculada (`invoice_date + meses_garantia`).
