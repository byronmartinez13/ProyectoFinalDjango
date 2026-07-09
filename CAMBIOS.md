# Historial de Cambios — SalesDjango

Cambios organizados por archivo, en orden de aplicación.

---

## `requirements.txt`

- `reportlab==4.5.1` — generación de PDFs
- `openpyxl==3.1.5` — exportación a Excel
- `pillow==12.2.0` — soporte de `ImageField` (fotos de productos, clientes, proveedores)
- `et-xmlfile==2.0.0` — dependencia de openpyxl
- `django-extensions==4.1` — utilidades de desarrollo (`shell_plus`, etc.)

---

## `config/settings.py`

- Añadido `MEDIA_URL = '/media/'` y `MEDIA_ROOT = BASE_DIR / 'media'` para servir archivos subidos por usuarios.
- Añadidos `'purchasing'` e `'inventory'` a `INSTALLED_APPS`.
- `LOGIN_REDIRECT_URL = '/dashboard/'` para redirigir al dashboard tras el login.

---

## `config/urls.py`

- `path('purchases/', include('purchasing.urls'))` — rutas del módulo de compras.
- `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` — sirve archivos media en desarrollo.

---

## `shared/money.py` *(creado)*

Función `round_money(value: Decimal) → Decimal` con `ROUND_HALF_UP` a 2 decimales.
Aplicada en todos los cálculos monetarios (`InvoiceDetail.save`, `PurchaseDetail.save`, `_recalc_invoice`, `purchase_create`).

---

## `shared/mixins.py`

- **`SearchListMixin`** — agrega búsqueda filtrada y paginación (`paginate_by = 10`) a cualquier `ListView` mediante `search_fields` declarativo. Inyecta `search_params` al contexto.
- **`ExportMixin`** — intercepta `?export=pdf` / `?export=excel` antes de paginar y genera el archivo con todos los registros del filtro activo usando `export_fields` y `export_filename`.
- **`SearchExportMixin`** — combina ambos mixins. Uso: `class MiListView(LoginRequiredMixin, SearchExportMixin, ListView)`.
- **`StaffRequiredMixin`** — protege las vistas de eliminación; solo usuarios con `is_staff = True` pueden acceder.

---

## `billing/models.py`

- **`Product`**: añadido campo `photo = ImageField(upload_to='products/')`, propiedad `balance = unit_price × stock`, campo `discount_pct` y campo `tax_rate`. Propiedad `photo_url` devuelve la URL de la foto o una imagen genérica por defecto.
- **`Invoice`**: añadido campo `estado` (0 Borrador / 1 Emitida / 2 Anulada) con propiedades `can_confirm`, `can_edit`, `can_delete`, `can_cancel`, `can_substitute`, `can_credit_note`.
- **`InvoiceDetail`**: añadido campo `discount_pct` (0–100, default 0). El método `save()` aplica el descuento al calcular `subtotal`.
- **`CreditNote`** *(nuevo modelo)*: vinculada a `Invoice` (FK PROTECT), campos: `date`, `tipo` ('total'/'parcial'), `amount`, `reason`, `is_active`.
- **`Customer`**: añadido campo `photo = ImageField(upload_to='customer/')` y propiedad `photo_url`.
- **`Supplier`**: añadido campo `photo = ImageField(upload_to='suppliers/')` y propiedad `photo_url`.

Migraciones asociadas: `0003_add_photo_to_product`, `0004_invoice_estado_creditnote`, `0005_backfill_invoice_estado`, `0006_invoicedetail_discount_pct`, `0007_product_tax_rate`, `0008_add_photo_customer_supplier`.

---

## `billing/forms.py`

- `ProductForm` eliminado y movido a `billing/ProductForm.py`.
- Añadido `CreditNoteForm`.
- `InvoiceDetailFormSet`: `extra=1, min_num=1, validate_min=True`, incluye `discount_pct`; `unit_price` con atributo `readonly`.

---

## `billing/ProductForm.py` *(creado)*

`ModelForm` independiente para `Product`. Incluye: widgets Bootstrap para todos los campos, labels en español, `help_texts`, `error_messages`, marcado automático `is-invalid` en `__init__`, validación `clean_unit_price` (precio > 0).

---

## `billing/CustomerForm.py` *(creado)*

Análogo a `ProductForm.py` para `Customer`. Campos: `dni`, `first_name`, `last_name`, `email`, `phone`, `address`, `is_active`, `photo`. Incluye `FileInput(class='d-none')` para control desde JS, marcado `is-invalid` automático.

---

## `billing/admin.py`

- Añadido `CreditNoteAdmin` con `list_display`, `list_filter`, `readonly_fields`.
- Añadido `CreditNoteInline` (TabularInline) en `InvoiceAdmin`.
- `InvoiceAdmin` con `readonly_fields = ('subtotal', 'tax', 'total')`.

---

## `billing/views.py`

- **`home`**: redirige al dashboard si el usuario ya está autenticado.
- **`dashboard`**: enriquecido con KPIs financieros (ventas totales, compras, margen bruto, stock bajo), top 5 productos por cantidad vendida, top 5 proveedores por monto, datos de ventas mensuales de los últimos 6 meses para Chart.js.
- **Refactorización de ListViews**: `BrandListView`, `ProductGroupListView`, `SupplierListView`, `ProductListView`, `CustomerListView`, `InvoiceListView` usan `SearchExportMixin`. `BrandListView` e `InvoiceListView` reemplazan FBVs anteriores.
- **`ProductCreateView` / `ProductUpdateView`**: usan `form_class = ProductForm` en lugar de `fields`.
- **`CustomerCreateView` / `CustomerUpdateView`**: usan `form_class = CustomerForm`, añadido `photo` a fields.
- **`SupplierCreateView` / `SupplierUpdateView`**: añadido `'photo'` a `fields`.
- **Nuevas vistas de factura**: `invoice_create`, `invoice_update`, `invoice_confirm` (descuenta stock con `F()` + `atomic()`), `invoice_cancel` (revierte stock), `invoice_substitute`, `credit_note_create`, `invoice_delete` (solo borradores).
- **`invoice_pdf`**: genera PDF con ReportLab (cabecera azul, datos del cliente, tabla de líneas con descuento e IVA, totales, notas de crédito).
- Función auxiliar `_recalc_invoice()` con `round_money`.
- Función auxiliar `_product_data_json()` para el autocompletado de precio en el formset.
- Import lazy de `purchasing.models.Purchase` dentro de `dashboard()` para evitar importación circular.

---

## `billing/urls.py`

- Rutas actualizadas a CBVs: `BrandListView`, `InvoiceListView`.
- Nuevas rutas: `invoices/<pk>/edit/`, `confirm/`, `cancel/`, `substitute/`, `credit-note/`, `pdf/`.
- Nueva ruta: `dashboard/`.

---

## `billing/templates/billing/base.html`

- Script de tema temprano en `<head>` (evita FOUC en modo oscuro).
- Toggle 🌙/☀️ en navbar con `localStorage`.
- Navbar en español con dropdown Ventas y enlace Compras.
- Modal genérico `#dmModal` con panel izquierdo (avatar / foto) y panel derecho (grilla de campos `.dm-field`).
- Función JS `showDetail(btn)`: lee atributos `data-dm-*` del botón, muestra la foto del registro si `data-dm-photo` está presente (círculo con sombra), o el avatar de iniciales si no hay foto. Botón Editar (`#dmEditLink`) y botón Ver detalle (`#dmDetailLink`) condicionales.
- Clases CSS añadidas: `.dm-avatar`, `.dm-field`, `.dm-label`, `.dm-value`, `.dm-divider`, `.inv-card-header`, `.inv-avatar`, `.cf-avatar`, `.pf-img-wrapper`, `.pf-img-cover`, `.pf-balance`, `.tbl-thumb-col`, `.tbl-thumb-cell`, `.tbl-thumb-img`.
- Variables Bootstrap (`--bs-tertiary-bg`, `--bs-border-color`, etc.) en lugar de colores hardcoded para compatibilidad con modo oscuro.

---

## `billing/templates/billing/home.html`

Reemplazado completamente por landing page pública de TecnoStock S.A.: sección Hero, Nosotros (Misión/Visión), Características (Ventas/Compras/Reportes/Seguridad) y Contacto ficticio.

---

## `billing/templates/billing/dashboard.html`

Reescrito con:
- KPIs financieros: ventas confirmadas, compras confirmadas, margen bruto, stock bajo.
- Contadores: productos, clientes, facturas.
- Gráfico de barras `#chartSales` (ventas mensuales, 6 meses) y gráfico donut `#chartEstados` (Borrador/Emitida/Anulada) con Chart.js CDN.
- Tablas de Top 5 productos (cabecera verde) y Top 5 proveedores (cabecera púrpura).
- Cards de acceso a módulos Ventas y Compras al pie.

---

## `billing/templates/billing/brand_list.html`

- Reescrito con `SearchExportMixin`: búsqueda por nombre/descripción y estado, exportación PDF/Excel, paginación.
- Botón "Ver" con `showDetail()` y campos: Nombre, Estado, Creado, Actualizado, Descripción.
- Botón "Editar" integrado en el modal (`data-dm-edit-url`); eliminado de la columna de acciones.

---

## `billing/templates/billing/productgroup_list.html`

Mismo patrón que `brand_list.html`. Campos en modal: Nombre, Estado, Creado, Actualizado. Traducido al español.

---

## `billing/templates/billing/supplier_list.html`

- Reescrito con búsqueda, paginación, exportación.
- Columna de miniatura circular (`.tbl-thumb-col` / `.tbl-thumb-img`) como primera columna.
- Botón "Ver" con `data-dm-photo` para mostrar logo en el modal. Campos: Empresa, Contacto, Email, Teléfono, Estado, Creado, Dirección.

---

## `billing/templates/billing/supplier_form.html`

- Añadido `enctype="multipart/form-data"` para soporte de subida de foto.

---

## `billing/templates/billing/product_list.html`

- Reescrito con búsqueda (nombre, marca, grupo, proveedor, precio min/max, stock min/max, estado), paginación, exportación.
- Columna Balance (`unit_price × stock`).
- Columna de miniatura circular con `data-dm-photo` para el modal.

---

## `billing/templates/billing/product_form.html`

Rediseño completo en dos columnas:
- **Izquierda**: nombre, marca/grupo, precio/stock, proveedores, switch activo, descripción.
- **Derecha**: zona de preview de imagen clickeable (`#pfImgWrapper`), tarjeta de balance dinámico.
- JS: preview con `FileReader`, recálculo de balance en tiempo real.

---

## `billing/templates/billing/customer_list.html`

- Reescrito con búsqueda, paginación, exportación. Traducido al español.
- Columna de miniatura circular con `data-dm-photo`.

---

## `billing/templates/billing/customer_form.html`

Rediseño completo en dos columnas:
- **Izquierda**: DNI, nombres/apellidos, email/teléfono, switch activo, dirección.
- **Derecha**: zona de foto clickeable con `FileReader` preview y badge de cámara; vista previa de campos en tiempo real.
- Añadido `enctype="multipart/form-data"`.

---

## `billing/templates/billing/invoice_list.html`

- Reescrito con búsqueda (cliente, fechas, total min/max, estado), paginación, exportación.
- Columna Estado con badge de color. Botón "Ver" con enlace al detalle completo.

---

## `billing/templates/billing/invoice_form.html`

- Rediseñado en dos cards (datos de factura + detalle de productos).
- Precio unitario `readonly` con autocompletado JS al seleccionar producto.
- Columna "Dto. (%)" editable; recálculo de subtotal en tiempo real.
- Botones "+ Agregar Fila" y "✕ Quitar".

---

## `billing/templates/billing/invoice_detail.html`

- Rediseñado en dos columnas: avatar/totales (izquierda) + datos del cliente y tabla de productos (derecha).
- Barra de botones condicional según `estado`: Emitir, Anular, Nota de Crédito, Sustituir, Editar, Eliminar.
- Sección de Notas de Crédito al pie.
- Botón PDF: `<a href="{% url 'billing:invoice_pdf' invoice.pk %}">`.

---

## `billing/templates/billing/invoice_confirm_emit.html` *(creado)*

Pantalla de confirmación antes de emitir: semáforo de stock por producto (rojo insuficiente / amarillo justo / verde holgado). Botón "Confirmar Emisión" deshabilitado si falta stock.

---

## `billing/templates/billing/credit_note_form.html` *(creado)*

Formulario de Nota de Crédito (tipo, monto, motivo) vinculado a la factura.

---

## `billing/templates/billing/_pagination.html` *(creado)*

Partial reutilizable de paginación Bootstrap: contador de registros, botones primera/anterior/siguiente/última, preserva parámetros de búsqueda activos.

---

## `billing/templates/billing/_export_buttons.html` *(creado)*

Partial reutilizable con botones PDF y Excel. La función JS `exportList(fmt)` añade `?export=pdf/excel` a la URL actual preservando los filtros.

---

## `purchasing/` *(app nueva)*

### `purchasing/models.py`

- **`Purchase`**: FK → `Supplier`, campos `document_number`, `purchase_date`, `subtotal`, `tax`, `total`, `estado` (BORRADOR / CONFIRMADA / ANULADA), `is_active`. `UniqueConstraint` sobre `(document_number, supplier)`.
- **`PurchaseDetail`**: FK → `Purchase` (CASCADE), FK → `Product` (PROTECT), campos `quantity`, `unit_cost`, `subtotal` (calculado en `save()` con `round_money`).
- **`SupplierCreditNote`**: nota de crédito de proveedor vinculada a una compra, campos `date`, `tipo`, `amount`, `reason`, `tax_amount`.

### `purchasing/forms.py`

- `PurchaseForm`: campos `supplier` y `document_number` con widgets Bootstrap.
- `PurchaseDetailForm`: campos `product`, `quantity`, `unit_cost` con clases CSS funcionales para el JS de recálculo.
- `PurchaseDetailFormSet = inlineformset_factory(...)`.

### `purchasing/views.py`

- **`purchase_list`**: `SearchExportMixin`, filtros por proveedor, fecha, estado; exportación PDF/Excel.
- **`purchase_create`**: valida formset, actualiza stock con `F('stock') + qty` dentro de `atomic()`, registra `StockMovement`.
- **`purchase_confirm`**: BORRADOR → CONFIRMADA.
- **`purchase_cancel`**: CONFIRMADA → ANULADA; revierte stock; registra `StockMovement`.
- **`purchase_detail`**: `select_related` + `prefetch_related` para optimizar queries.
- **`purchase_delete`**: elimina solo BORRADORES.
- **`purchase_pdf`**: genera PDF con ReportLab (cabecera púrpura, datos del proveedor, tabla de líneas con IVA, totales, notas de crédito del proveedor).
- **`supplier_credit_note_create`**: crea `SupplierCreditNote` vinculada a la compra.

### `purchasing/urls.py`

`app_name='purchasing'`. Rutas: listado, crear, detalle, confirmar, anular, eliminar, PDF, nota de crédito.

### `purchasing/templates/purchasing/`

| Template | Descripción |
|---|---|
| `purchase_list.html` | Lista con filtros, paginación y exportación |
| `purchase_form.html` | Formset con recálculo JS en tiempo real |
| `purchase_detail.html` | Detalle en dos columnas; botones confirmar/anular/PDF |
| `purchase_confirm.html` | Confirmación de emisión de compra |
| `purchase_cancel.html` | Confirmación de anulación de compra |
| `purchase_confirm_delete.html` | Confirmación de eliminación |
| `supplier_credit_note_form.html` | Formulario de nota de crédito de proveedor |

---

## `inventory/` *(app nueva)*

### `inventory/models.py`

- **`StockMovement`**: registro inmutable de cada movimiento de stock. Campos: FK → `Product`, `quantity` (+ entrada / − salida), `movement_type` (VENTA / DEV_VENTA / COMPRA / DEV_COMPRA / ENT_MANUAL / SAL_MANUAL), `date` (auto), FK → `User` (nullable), FK opcional → `Invoice`, FK opcional → `Purchase`, `notes`.
- Registra automáticamente un movimiento al confirmar o anular facturas y compras.
