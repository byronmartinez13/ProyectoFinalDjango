# TecnoStock S.A. — Sistema de Ventas, Compras y Tienda en Línea

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/Django-6.x-darkgreen?style=for-the-badge&logo=django">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap">
  <img src="https://img.shields.io/badge/PayPal-Checkout-003087?style=for-the-badge&logo=paypal">
  <img src="https://img.shields.io/badge/SQLite-Base_de_Datos-lightblue?style=for-the-badge&logo=sqlite">
  <img src="https://img.shields.io/badge/Estado-En_Desarrollo-orange?style=for-the-badge">
</p>

---

## Descripción

Proyecto académico desarrollado para la asignatura de **Programación Orientada a Objetos con Python**, utilizando el framework **Django** y el entorno de desarrollo **Visual Studio Code**.

Es un sistema web para la empresa ficticia **TecnoStock S.A.** que integra cuatro módulos principales:

- **Módulo de Ventas** — gestión de marcas, grupos, proveedores, productos, clientes y facturación con ciclo de vida completo.
- **Módulo de Compras** — registro de compras a proveedores con actualización automática de inventario.
- **Módulo de Seguridad** — usuarios, roles (Grupos de Django) y una matriz de permisos por rol, con login anclado a rol y recuperación de contraseña.
- **Tienda en línea (Cliente)** — catálogo público, carrito de compras y checkout con pago real por PayPal o tarjeta.

---

## Objetivos del Proyecto

- Aplicar el patrón MVT (Modelo - Vista - Template) de Django
- Implementar relaciones entre modelos (ForeignKey, OneToOne, ManyToMany)
- Gestionar autenticación, roles y permisos de usuarios de forma granular
- Aplicar vistas basadas en funciones (FBV) y en clases (CBV)
- Reutilizar código mediante mixins, decoradores y validadores compartidos
- Implementar formularios con formsets para documentos con detalle (facturas, compras)
- Organizar un proyecto Django multi-app de forma profesional
- Implementar ciclo de vida de documentos contables (Borrador → Emitida → Anulada)
- Gestionar stock con expresiones atómicas `F()` del ORM de Django
- Integrar un flujo de pago real (PayPal Checkout) desde una tienda orientada al cliente final
- Enviar correo transaccional (bienvenida y recuperación de contraseña) vía SMTP

---

## Roles del Sistema

Los roles se implementan con el sistema de `Group`/`Permission` nativo de Django (no hay un modelo de rol propio). Se crean con `python manage.py setup_roles` y se administran desde **Seguridad → Permisos** (matriz por rol) y **Seguridad → Roles**.

| Rol                     | Alcance                                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------------------------|
| **Administrador**       | Control total del sistema: usuarios, roles, permisos, y todos los módulos de Ventas y Compras.             |
| **Vendedor**            | Ve productos (precio/stock, sin editar ni eliminar). Clientes: crear, editar, ver (no eliminar). Facturas: crear, ver, editar borradores (no anular). Sin acceso al módulo de Compras. |
| **Analista de Compras** | Marcas/Grupos/Productos: crear, editar, ver (no eliminar). Proveedores: control total (incluye eliminar). Compras: control total. Facturas: solo ver y anular (no crear ni editar). |
| **Cliente**             | Rol de autoregistro público. Ve el catálogo de productos activos, arma su carrito y paga por PayPal o tarjeta. Sin acceso a los módulos administrativos. |

> Las cuentas creadas antes de introducir el sistema de roles (sin ningún `Group` asignado) conservan acceso completo por compatibilidad (`GroupRequiredMixin` en modo no estricto), salvo en las acciones explícitamente restringidas a Administrador.

---

## Tecnologías Utilizadas

| Tecnología          | Uso                                                          |
|----------------------|---------------------------------------------------------------|
| Python 3            | Lenguaje principal                                             |
| Django 6            | Framework web (MVT)                                            |
| Bootstrap 5.3       | Estilos, componentes UI y modo claro/oscuro                    |
| Chart.js            | Gráficos del dashboard (barras y donut)                        |
| SQLite              | Base de datos de desarrollo                                    |
| ReportLab           | Exportación a PDF de facturas y compras                        |
| OpenPyXL            | Exportación a Excel                                            |
| Pillow              | Gestión de imágenes (`ImageField`)                             |
| PayPal Checkout SDK | Pago real (sandbox) con botones de PayPal y de Tarjeta         |
| `requests`          | Cliente HTTP para la API REST v2 de PayPal                     |
| `python-dotenv`     | Carga de variables de entorno desde `.env`                     |
| Gmail SMTP          | Envío de correos de bienvenida y de recuperación de contraseña |
| Visual Studio Code  | Entorno de desarrollo                                          |
| Git / GitHub        | Control de versiones                                           |

---

## Estructura del Proyecto

```text
ProyectoFinCursoDjango/
│
├── manage.py                        ← Punto de entrada Django
├── requirements.txt                 ← Dependencias del proyecto
├── .env                             ← Variables de entorno reales (fuera de git)
├── .env.example                     ← Plantilla de variables de entorno
├── CAMBIOS.md                       ← Historial de cambios por archivo
├── .gitignore
│
├── config/                          ← Configuración del proyecto
│   ├── settings.py                  ← Carga .env, EMAIL_*, PAYPAL_*, INSTALLED_APPS
│   ├── urls.py                      ← Login por rol, password_reset por usuario, apps
│   ├── wsgi.py
│   └── asgi.py
│
├── billing/                         ← App de Ventas (módulo principal)
│   ├── models.py                    ← Brand, ProductGroup, Supplier, Product,
│   │                                   Customer (+ user OneToOne), Invoice
│   │                                   (+ payment_method, paypal_order_id),
│   │                                   InvoiceDetail, CreditNote
│   ├── views.py                     ← FBV (facturas, PDF) + CBV (resto), restringidas por rol
│   ├── services.py                  ← check_stock(), emit_invoice(), recalc_invoice()
│   │                                   (reutilizado por Ventas y por el checkout de la Tienda)
│   ├── forms.py                     ← SignUpForm (Admin, con selector de rol), BrandForm,
│   │                                   InvoiceForm, InvoiceDetailFormSet, CreditNoteForm
│   ├── ProductForm.py               ← Formulario avanzado de Producto
│   ├── CustomerForm.py              ← Formulario avanzado de Cliente (con foto)
│   ├── urls.py                      ← Rutas de la app de ventas
│   ├── admin.py                     ← Registro con inlines y filtros
│   ├── migrations/
│   └── templates/billing/
│       ├── base.html                ← Layout base: navbar por rol, modal detalle, modo oscuro
│       ├── home.html                ← Landing page pública (TecnoStock S.A.)
│       ├── dashboard.html           ← KPIs, Chart.js, top productos/proveedores
│       ├── brand_*.html, productgroup_*.html, supplier_*.html
│       ├── product_*.html           ← Lista con foto, formulario con preview
│       ├── customer_*.html          ← Lista con foto, formulario con preview en vivo
│       ├── invoice_*.html           ← Lista, formulario, detalle, confirmar emisión,
│       │                               anular, sustituir, PDF
│       ├── credit_note_form.html    ← Formulario de Nota de Crédito
│       ├── _pagination.html         ← Partial reutilizable de paginación
│       └── _export_buttons.html     ← Partial reutilizable de exportación
│
├── purchasing/                      ← App de Compras (solo Administrador / Analista de Compras)
│   ├── models.py                    ← Purchase, PurchaseDetail, SupplierCreditNote
│   ├── views.py                     ← list, create, confirm, cancel, detail, delete, pdf
│   ├── forms.py                     ← PurchaseForm, PurchaseDetailForm, FormSet
│   ├── urls.py, admin.py, migrations/
│   └── templates/purchasing/        ← Lista, formulario, detalle, confirmar, anular, PDF
│
├── inventory/                       ← App de Inventario (solo modelos y admin)
│   ├── models.py                    ← StockMovement (auditoría de movimientos)
│   ├── admin.py
│   └── migrations/
│
├── security/                        ← App de Seguridad: usuarios, roles y permisos
│   ├── models.py                    ← Vacío a propósito: usa auth.User/Group/Permission
│   ├── views.py                     ← RoleSelectLoginView, RoleLoginView,
│   │                                   UsernamePasswordResetView, CRUD de Usuarios/
│   │                                   Roles/Permisos (todo AdminOnlyMixin)
│   ├── forms.py                     ← UserUpdateForm, GroupForm, PermissionForm,
│   │                                   UsernamePasswordResetForm
│   ├── urls.py
│   ├── management/commands/setup_roles.py  ← Crea/actualiza los 4 roles y sus permisos
│   ├── templatetags/security_tags.py       ← Filtros {{ user|has_group:'X' }}
│   └── templates/security/
│       ├── role_select.html         ← Selector de rol por tarjetas (login)
│       ├── role_login.html          ← Login anclado a un rol, con mostrar/ocultar clave
│       ├── user_list.html, user_form.html
│       ├── group_list.html, group_form.html
│       ├── permission_list.html     ← Matriz de permisos por rol (checkboxes + "marcar todos")
│       ├── permission_form.html
│       └── confirm_delete.html
│
├── store/                           ← App de Tienda (rol Cliente)
│   ├── models.py                    ← Cart (OneToOne → Customer), CartItem
│   ├── forms.py                     ← CustomerSignUpForm (registro público),
│   │                                   CompleteProfileForm
│   ├── views.py                     ← CustomerSignUpView, CatalogView (búsqueda +
│   │                                   categorías), carrito, checkout, endpoints
│   │                                   AJAX de PayPal, confirmación de pedido
│   ├── paypal.py                    ← Wrapper del REST API v2 de PayPal (token,
│   │                                   crear orden, capturar orden)
│   ├── urls.py, admin.py, migrations/
│   └── templates/store/
│       ├── customer_signup.html     ← Registro público (con mostrar/ocultar clave)
│       ├── complete_profile.html    ← Completa datos de facturación si faltan
│       ├── catalog.html             ← Catálogo con barra de búsqueda y sidebar de categorías
│       ├── cart.html                ← Carrito con cantidad editable por línea
│       ├── checkout.html            ← Resumen + botones PayPal / Tarjeta (PayPal SDK)
│       └── order_confirmation.html
│
├── shared/                          ← Código reutilizable (no es una app Django)
│   ├── __init__.py
│   ├── mixins.py                    ← SearchListMixin, ExportMixin, SearchExportMixin,
│   │                                   StaffRequiredMixin, GroupRequiredMixin,
│   │                                   AdminOnlyMixin, ClienteRequiredMixin
│   ├── money.py                     ← round_money() con ROUND_HALF_UP
│   ├── decorators.py                ← @audit_action, roles_required(), @cliente_required
│   ├── emails.py                    ← send_welcome_email()
│   └── validators.py                ← validate_cedula_ec
│
└── templates/                       ← Templates globales
    └── registration/
        ├── login.html                       ← Login clásico (fallback sin roles configurados)
        ├── signup.html                      ← Alta de usuario por el Administrador
        ├── password_change_form.html, password_change_done.html
        ├── password_reset_form.html         ← Pide el nombre de usuario (no el email)
        ├── password_reset_done.html
        ├── password_reset_confirm.html      ← Nueva contraseña (mostrar/ocultar)
        ├── password_reset_complete.html
        ├── password_reset_email.html        ← Cuerpo del correo de recuperación
        └── password_reset_subject.txt
```

---

## Modelos y Relaciones

### App `billing` (Ventas)

| Modelo          | Relaciones y notas                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------------------|
| `Brand`         | —                                                                                                          |
| `ProductGroup`  | —                                                                                                          |
| `Supplier`      | Campo `photo` (ImageField)                                                                                 |
| `Product`       | FK → Brand, FK → ProductGroup, M2M → Supplier. Campos: `photo`, `tax_rate`, `stock`, `is_active`          |
| `Customer`      | Campo `photo`. **`user`**: OneToOne opcional → `auth.User` (vincula la cuenta de un Cliente autoregistrado con su ficha de facturación) |
| `Invoice`       | FK → Customer. `estado`: Borrador(0) / Emitida(1) / Anulada(2). **`payment_method`** ('card'/'paypal') y **`paypal_order_id`**: solo se llenan cuando la factura nace de un checkout online |
| `InvoiceDetail` | FK → Invoice, FK → Product. Campo `discount_pct`                                                          |
| `CreditNote`    | FK → Invoice. Tipos: Devolución Total / Parcial                                                            |

### App `purchasing` (Compras)

| Modelo               | Relaciones y notas                                                 |
|----------------------|--------------------------------------------------------------------|
| `Purchase`           | FK → Supplier. `estado`: Borrador / Confirmada / Anulada           |
| `PurchaseDetail`     | FK → Purchase (CASCADE), FK → Product (PROTECT)                   |
| `SupplierCreditNote` | FK → Purchase. Nota de crédito emitida por el proveedor            |

### App `inventory` (Inventario)

| Modelo          | Relaciones y notas                                                              |
|-----------------|-----------------------------------------------------------------------------------|
| `StockMovement` | FK → Product, FK opcional → Invoice, FK opcional → Purchase, FK opcional → User    |

### App `store` (Tienda del Cliente)

| Modelo     | Relaciones y notas                                                                 |
|------------|--------------------------------------------------------------------------------------|
| `Cart`     | OneToOne → `billing.Customer`. Propiedades `subtotal`, `tax`, `total`, `items_count` |
| `CartItem` | FK → Cart (CASCADE), FK → Product. `unique_together = (cart, product)`              |

> El checkout **no crea un modelo de "Pedido" aparte**: al capturar el pago se genera directamente un `Invoice` + `InvoiceDetail` (mismo ciclo de vida Borrador → Emitida que usa Ventas), reutilizando `billing/services.py` para descontar stock y registrar `StockMovement`.

> `Supplier` y `Product` son compartidos entre apps; `purchasing`, `inventory` y `store` los importan de `billing.models`.

---

## Funcionalidades del Sistema

### Módulo de Ventas

| Sección      | Operaciones                                                                        |
|--------------|------------------------------------------------------------------------------------|
| Marcas       | Listar, Crear, Editar, Ver detalle, Exportar PDF/Excel — Eliminar solo Administrador |
| Grupos       | Listar, Crear, Editar, Ver detalle, Exportar PDF/Excel — Eliminar solo Administrador |
| Proveedores  | Listar, Crear, Editar, Eliminar, Ver detalle, Exportar — control total para Administrador y Analista de Compras |
| Productos    | Listar (con foto), Crear, Editar (balance dinámico), Ver detalle, Exportar — Eliminar solo Administrador; Vendedor solo puede ver |
| Clientes     | Listar (con foto), Crear, Editar (preview en vivo), Ver detalle, Exportar — Eliminar solo Administrador/Staff |
| Facturas     | Listar, Crear borrador, Emitir, Ver detalle, Sustituir, Nota de Crédito, PDF, Exportar — Crear/Editar solo Administrador y Vendedor; Anular solo Administrador y Analista de Compras |

#### Ciclo de vida de facturas

```
Nueva Factura ──► Borrador ──► Emitir ──► Emitida ──► Anular ──► Anulada
                    │                        │
                  Editar                   Sustituir → nuevo Borrador
                  Eliminar                 Nota de Crédito
```

- **Borrador** — se puede editar y eliminar; el stock **no** se modifica.
- **Emitida** — el stock se descuenta automáticamente al emitir; solo se puede anular, crear nota de crédito o sustituir.
- **Anulada** — el stock se revierte automáticamente; registro histórico visible e inactivo.
- **Nota de Crédito** — documento contable vinculado a la factura original (devolución parcial o total).
- **Sustitución** — anula la factura original y crea un nuevo borrador con los mismos datos para corregir y volver a emitir.
- La emisión (descuento de stock + `StockMovement`) vive en `billing/services.py::emit_invoice()`, compartida entre la emisión manual (Vendedor/Administrador) y el checkout online de la Tienda.

### Módulo de Compras

Acceso exclusivo de **Administrador** y **Analista de Compras** (bloqueado a nivel de servidor, no solo oculto en el menú).

| Sección            | Operaciones                                                                         |
|--------------------|-------------------------------------------------------------------------------------|
| Compras            | Listar, Crear borrador, Confirmar, Anular, Ver detalle, Descargar PDF, Exportar     |
| Nota de crédito    | Registrar nota de crédito del proveedor vinculada a la compra                       |

#### Ciclo de vida de compras

```
Nueva Compra ──► Borrador ──► Confirmar ──► Confirmada ──► Anular ──► Anulada
                   │
                 Eliminar
```

- **Borrador** — editable; stock no modificado.
- **Confirmada** — stock incrementado automáticamente con `F()` + `atomic()`; registra `StockMovement`.
- **Anulada** — stock revertido; registra `StockMovement`.

### Módulo de Seguridad (Administrador)

| Sección              | Descripción                                                                                     |
|----------------------|----------------------------------------------------------------------------------------------------|
| Usuarios             | Listar, editar datos y roles, eliminar. Alta de nuevas cuentas (`+ Nuevo Usuario`) con cualquier rol — envía correo de bienvenida con usuario, contraseña y rol asignado |
| Roles                | Crear/editar/eliminar roles (`Group`) y sus permisos con checkboxes                              |
| Permisos             | Crear/editar/eliminar permisos personalizados + **matriz de permisos por rol**: cada fila es un permiso, cada columna un rol, con checkbox por celda y un checkbox "marcar/desmarcar todos" por rol |
| Login por rol        | `/accounts/login/` muestra una tarjeta por rol; cada tarjeta lleva a un login anclado a ese rol (rechaza credenciales válidas si la cuenta no tiene ese rol) |
| Recuperar contraseña | El usuario ingresa su **nombre de usuario**; si existe, se envía un correo (a la dirección ya registrada) con un enlace único para elegir una nueva contraseña. Funciona para cuentas autoregistradas y para las creadas por el Administrador |

### Tienda en línea (Cliente)

| Sección           | Descripción                                                                                          |
|-------------------|----------------------------------------------------------------------------------------------------------|
| Registro público  | Formulario en la página de inicio (`/tienda/registro/`): crea la cuenta con rol Cliente, la vincula a un `Customer` y envía el correo de bienvenida. Inicia sesión automáticamente |
| Catálogo          | Solo productos activos; sin columnas de balance/estado; barra de búsqueda (nombre/descripción/marca) y sidebar de categorías; botón "Añadir al carrito" (deshabilitado si no hay stock) |
| Carrito           | Cantidad editable por línea (limitada al stock disponible), quitar producto, subtotal/IVA/total |
| Checkout          | Botones reales de **PayPal** y de **Tarjeta de débito/crédito** (PayPal Checkout con `enable-funding=card`, mismo SDK) |
| Confirmación      | Al capturar el pago se genera la factura, se descuenta el stock y se vacía el carrito                |

---

## Configuración de variables de entorno (`.env`)

El proyecto usa `python-dotenv` para cargar configuración sensible desde un archivo `.env` (ignorado por git). Copia `.env.example` como `.env` y completa:

```dotenv
# Email (si se deja vacío, los correos se imprimen en consola en vez de enviarse)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=contraseña_de_aplicación_de_16_caracteres
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=TecnoStock <tu_correo@gmail.com>

# PayPal (crear una app en https://developer.paypal.com/ → Sandbox → Apps)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox
```

> Para Gmail, `EMAIL_HOST_PASSWORD` debe ser una **contraseña de aplicación** (requiere verificación en 2 pasos activada), no la contraseña normal de la cuenta.

---

## Características Transversales

| Característica            | Descripción                                                                          |
|---------------------------|--------------------------------------------------------------------------------------|
| Autenticación por rol      | Login con tarjetas de rol; cada rol solo entra por su propia tarjeta               |
| Recuperación de contraseña | Por nombre de usuario, con correo real vía SMTP                                     |
| Correo transaccional       | Bienvenida (usuario/contraseña/rol) y recuperación de contraseña, vía Gmail SMTP     |
| Control de permisos        | `GroupRequiredMixin` / `AdminOnlyMixin` / `ClienteRequiredMixin` / `roles_required()` protegen cada vista en el servidor, no solo el menú |
| Matriz de permisos         | Asignar/quitar permisos de todos los roles desde una sola pantalla                   |
| Pago real en línea         | PayPal Checkout (sandbox) con dos opciones: cuenta PayPal o tarjeta                  |
| Auditoría de stock         | `StockMovement` registra cada entrada/salida con tipo, usuario, fecha y documento    |
| Búsqueda y filtros         | Buscador por múltiples campos + filtros por fecha, estado, rango de precios/categoría |
| Paginación                 | Paginación automática en todos los listados                                         |
| Exportación                | Botones PDF y Excel en los módulos administrativos                                  |
| PDF de documentos          | Facturas y compras exportables a PDF con ReportLab                                  |
| Modal de detalle           | Botón "Ver" abre modal con foto/avatar, datos del registro y botón Editar integrado |
| Mostrar/ocultar contraseña | Registro, login y cambio/recuperación de contraseña                                 |
| Modo oscuro / claro        | Toggle en la barra de navegación; preferencia guardada en `localStorage`             |
| Validación de cédula       | Validador `validate_cedula_ec` con algoritmo oficial del Registro Civil del Ecuador  |
| Landing page pública       | Página de inicio de TecnoStock S.A. sin requerir login                              |
| Dashboard con KPIs         | Ventas/compras/margen bruto, gráficos Chart.js, top 5 productos y proveedores (Cliente es redirigido a la tienda en vez de ver este panel) |

---

## Carpeta `shared/` — Código Reutilizable

### `SearchListMixin` / `ExportMixin` / `SearchExportMixin`
Búsqueda declarativa + paginación + exportación PDF/Excel para cualquier `ListView` (usado también por el catálogo de la Tienda).

### `StaffRequiredMixin`
Protege vistas de eliminación heredadas del esquema anterior: solo `is_staff = True`.

### `GroupRequiredMixin` / `AdminOnlyMixin` / `ClienteRequiredMixin`
Restringen vistas por rol (`Group`). `AdminOnlyMixin` exige el rol Administrador sin excepciones; `ClienteRequiredMixin` exige el rol Cliente; `GroupRequiredMixin` es la base configurable (`group_required`, `strict`) que usan las vistas de Marcas/Grupos/Proveedores/Productos/Compras.

### `roles_required()` / `cliente_required` (decoradores)
Equivalentes a los mixins anteriores pero para vistas basadas en función (usados en `purchasing/views.py`, `billing/views.py` y `store/views.py`).

### `@audit_action`
Decorador que registra en el logger `audit` cada acción importante: usuario, acción, IP, método HTTP y timestamp.

### `send_welcome_email()`
Envía el correo de bienvenida (usuario, contraseña, rol) tanto en el alta por el Administrador como en el autoregistro público.

### `validate_cedula_ec`
Valida que el campo `dni` sea matemáticamente correcto según el algoritmo del Registro Civil del Ecuador.

---

## Ejecución del Proyecto

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ProyectoFinCursoDjango
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac / Linux:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
copy .env.example .env      # Windows
cp .env.example .env        # Mac / Linux
```

Completa `.env` con tus credenciales de Gmail SMTP y de PayPal Sandbox (ver sección anterior).

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear los roles del sistema

```bash
python manage.py setup_roles
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Iniciar el servidor

```bash
python manage.py runserver
```

Abrir el navegador en `http://127.0.0.1:8000`. El registro público de Clientes está en `http://127.0.0.1:8000/tienda/registro/` (enlazado desde la landing page).

---

## Dependencias principales (`requirements.txt`)

```
Django==6.0.6
reportlab==4.5.1
openpyxl==3.1.5
pillow==12.2.0
django-extensions==4.1
python-dotenv==1.2.2
requests==2.34.2
```

> No se necesita instalar nada adicional; todas las dependencias ya están declaradas en `requirements.txt`.

---

## Uso de Inteligencia Artificial

Durante el desarrollo del proyecto se utilizó **Claude (Anthropic)** como herramienta de apoyo para:

- Revisar que el proyecto cumpliera los requisitos de la guía de la tarea
- Resolver dudas sobre relaciones entre modelos y el ORM de Django
- Orientación en la implementación de `inlineformset_factory` para facturas y compras con detalle
- Apoyo en la implementación de mixins reutilizables (`SearchExportMixin`)
- Implementación del ciclo de vida de facturas (Borrador / Emitida / Anulada)
- Uso de expresiones `F()` para actualizaciones atómicas de stock
- Diseño del módulo de Compras y la landing page pública
- Diseño e implementación del sistema de roles (Cliente, Vendedor, Analista de Compras, Administrador) y su matriz de permisos
- Integración de correo transaccional (bienvenida y recuperación de contraseña) vía SMTP
- Implementación de la Tienda en línea: catálogo con búsqueda y categorías, carrito y checkout
- Integración real con PayPal Checkout (pago con cuenta PayPal o con tarjeta) mediante su API REST v2
- Generación del `.gitignore`, `CAMBIOS.md` y este `README`

### Ejemplos de prompts utilizados

**Prompt 1**
```
cual sería la mejor forma de maximizar el rendimiento del progarma y minimizar el codigo, manteniendolo compacto y funcional.
```

**Prompt 2**
```
Implementa las funciones alternativas para el módulo de facturación:
botón Anular que revierte el stock, módulo de Notas de Crédito vinculado
a la factura original, y flujo de Sustitución que anula la factura vieja
y crea un borrador editable. Agrega un campo estado en la tabla facturas
(0=Borrador, 1=Emitida, 2=Anulada).
```

**Prompt 3**
```
¿Cómo aplico el StaffRequiredMixin en las vistas de eliminación
y cuál es el orden correcto de herencia en Django CBV?
```

**Prompt 4**
```
Hay que crear otro rol, ese rol va a ser customer... además necesito que
cada que se cree una cuenta nueva se envíe un correo al email ingresado...
el cliente podrá ver los productos pero no editarlos ni eliminarlos... debe
haber un botón para añadir al carrito y 2 opciones de pago: tarjeta o PayPal.
```

**Prompt 5**
```
Para el rol de administrador, en la pantalla de permisos muestra también
los roles y un checkbox en cada línea de permisos, para asignar o quitar
permisos por rol, con un checkbox que marque/desmarque todos los de esa
columna.
```

---

## Equipo de Desarrollo

| Nombre                     | Rol              |
|----------------------------|------------------|
| Vera Paredes Daniel        | Profesor         |
| Delgado Zambrano Alexy     | 4to semestre     |
| Gines Moncada Brithany     | 4to semestre     |
| López Herrera Ashley       | 4to semestre     |
| Martínez López Byron       | 4to semestre     |
| Moreira Intriago Diego     | 4to semestre     |
| Quizhpi Landi Andy         | 4to semestre     |

---

> Si el proyecto te resulta útil, puedes darle una ⭐ al repositorio para apoyar el trabajo realizado.
