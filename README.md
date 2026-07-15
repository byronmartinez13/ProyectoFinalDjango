# TecnoStock S.A. — Sistema de Ventas, Compras y Tienda en Línea

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/Django-6.x-darkgreen?style=for-the-badge&logo=django">
  <img src="https://img.shields.io/badge/FastAPI-Microservicios-009688?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap">
  <img src="https://img.shields.io/badge/PayPal-Checkout-003087?style=for-the-badge&logo=paypal">
  <img src="https://img.shields.io/badge/SQLite-Base_de_Datos-lightblue?style=for-the-badge&logo=sqlite">
  <img src="https://img.shields.io/badge/Estado-En_Desarrollo-orange?style=for-the-badge">
</p>

---

## Descripción

Proyecto académico desarrollado para la asignatura de **Programación Orientada a Objetos con Python**, utilizando el framework **Django** y el entorno de desarrollo **Visual Studio Code**.

Es un sistema para la empresa ficticia **TecnoStock S.A.** compuesto por **tres proyectos independientes** en el mismo repositorio (monorepo):

| Carpeta                      | Tecnología      | Rol                                                                                 |
|-------------------------------|-----------------|--------------------------------------------------------------------------------------|
| [`ProyectoDjango/`](ProyectoDjango/)             | Django 6        | Aplicación principal: Ventas, Compras, Inventario, Seguridad, Tienda en línea, Cuentas por Cobrar/Pagar |
| [`microservicio_pagos/`](microservicio_pagos/)        | FastAPI         | Simula el procesamiento de un pago (Sandbox) y notifica por correo al cliente        |
| [`microservicio_facturacion/`](microservicio_facturacion/)  | FastAPI         | Simula la autorización de una factura electrónica ante el SRI (Ecuador) y notifica por correo al cliente |

Los dos microservicios son **HTTP API independientes**: no comparten base de datos ni código con Django, se llaman por `requests` una vez que la operación ya quedó confirmada en la BD local de Django, y su caída **nunca revierte una venta, factura o abono** (fallan en silencio y solo dejan un registro en el log — ver [`shared/microservicios.py`](ProyectoDjango/shared/microservicios.py)).

El proyecto integra los siguientes módulos dentro de Django:

- **Módulo de Ventas** — gestión de marcas, grupos, proveedores, productos, clientes y facturación con ciclo de vida completo, con venta al **Contado** o a **Crédito**.
- **Módulo de Compras** — registro de compras a proveedores con actualización automática de inventario, también a Contado o a Crédito.
- **Cuentas por Cobrar** (`creditoventa`) — registro de abonos sobre facturas de venta a crédito y su historial.
- **Cuentas por Pagar** (`pagos`) — registro de abonos sobre compras a proveedores a crédito y su historial. *(No confundir con el microservicio `microservicio_pagos`, que es un servicio HTTP aparte — ver [nota de nombres](#nota-sobre-nombres-parecidos-app-pagos-vs-microservicio_pagos).)*
- **Módulo de Seguridad** — usuarios, roles (Grupos de Django) y una matriz de permisos por rol, con login anclado a rol y recuperación de contraseña.
- **Tienda en línea (Cliente)** — catálogo público, carrito de compras y checkout con pago real por PayPal o tarjeta.
- **Facturación electrónica** — al emitir cualquier factura (venta manual o checkout de la Tienda), Django genera y envía el PDF de la factura por correo, y además delega al `microservicio_facturacion` la simulación de autorización SRI (clave de acceso + XML del comprobante) enviada también por correo.

---

## Objetivos del Proyecto

- Aplicar el patrón MVT (Modelo - Vista - Template) de Django
- Implementar relaciones entre modelos (ForeignKey, OneToOne, ManyToMany)
- Gestionar autenticación, roles y permisos de usuarios de forma granular
- Aplicar vistas basadas en funciones (FBV) y en clases (CBV)
- Reutilizar código mediante mixins, decoradores y validadores compartidos
- Implementar formularios con formsets para documentos con detalle (facturas, compras)
- Organizar un proyecto Django multi-app de forma profesional
- Implementar ciclo de vida de documentos contables (Borrador → Emitida/Confirmada → Anulada)
- Gestionar ventas y compras a **Contado** o a **Crédito**, con cuentas por cobrar/pagar y abonos progresivos
- Gestionar stock con expresiones atómicas `F()` del ORM de Django
- Integrar un flujo de pago real (PayPal Checkout) desde una tienda orientada al cliente final
- Enviar correo transaccional (bienvenida, recuperación de contraseña, facturación electrónica, confirmación de pago y de abonos) vía SMTP
- Diseñar una arquitectura de **microservicios independientes** (FastAPI) que se comunican con Django por HTTP sin acoplar base de datos ni código
- Aplicar validaciones de negocio de extremo a extremo: formato (cédula/RUC, teléfono, nombres), campos obligatorios/vacíos, rangos numéricos y fechas, y reglas contra el estado real de los datos (saldos, stock)

---

## Roles del Sistema

Los roles se implementan con el sistema de `Group`/`Permission` nativo de Django (no hay un modelo de rol propio). Se crean con `python manage.py setup_roles` y se administran desde **Seguridad → Permisos** (matriz por rol) y **Seguridad → Roles**.

| Rol                     | Alcance                                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------------------------|
| **Administrador**       | Control total del sistema: usuarios, roles, permisos, y todos los módulos de Ventas y Compras.             |
| **Vendedor**            | Ve productos (precio/stock, sin editar ni eliminar). Clientes: crear, editar, ver (no eliminar). Facturas: crear, ver, editar borradores, emitir a Contado o Crédito (no anular). Registra cobros sobre facturas a crédito (`creditoventa`). Sin acceso al módulo de Compras. |
| **Analista de Compras** | Marcas/Grupos/Productos: crear, editar, ver (no eliminar). Proveedores: control total (incluye eliminar). Compras: control total (Contado/Crédito). Registra pagos sobre compras a crédito (`pagos`). Facturas: solo ver y anular (no crear ni editar). |
| **Cliente**             | Rol de autoregistro público. Ve el catálogo de productos activos, arma su carrito y paga por PayPal o tarjeta. Sin acceso a los módulos administrativos. |

> Las cuentas creadas antes de introducir el sistema de roles (sin ningún `Group` asignado) conservan acceso completo por compatibilidad (`GroupRequiredMixin` en modo no estricto), salvo en las acciones explícitamente restringidas a Administrador.

---

## Tecnologías Utilizadas

| Tecnología          | Uso                                                          |
|----------------------|---------------------------------------------------------------|
| Python 3            | Lenguaje principal                                             |
| Django 6            | Framework web (MVT) de la aplicación principal                 |
| FastAPI + Uvicorn   | Microservicios independientes de Pagos y Facturación Electrónica |
| Pydantic            | Validación de los payloads de los microservicios               |
| Bootstrap 5.3       | Estilos, componentes UI y modo claro/oscuro                    |
| Chart.js            | Gráficos del dashboard (barras y donut)                        |
| SQLite              | Base de datos de desarrollo (solo la usa Django)                |
| ReportLab           | Exportación a PDF de facturas y compras                        |
| OpenPyXL            | Exportación a Excel                                            |
| Pillow              | Gestión de imágenes (`ImageField`)                              |
| PayPal Checkout SDK | Pago real (sandbox) con botones de PayPal y de Tarjeta         |
| `requests`          | Cliente HTTP de Django hacia la API REST v2 de PayPal y hacia los microservicios propios |
| `python-dotenv`     | Carga de variables de entorno desde `.env` (en los tres proyectos) |
| Gmail SMTP          | Envío de correos (bienvenida, recuperación de contraseña, factura, pago, abono) |
| Visual Studio Code  | Entorno de desarrollo                                          |
| Git / GitHub        | Control de versiones                                           |

---

## Estructura del Repositorio

```text
ProyectoFinalDjango/                      ← Raíz del repositorio (monorepo)
│
├── README.md                             ← Este archivo
├── .gitignore                            ← Ignora venv/, __pycache__/, .env, .claude/ en cualquier subcarpeta
│
├── ProyectoDjango/                       ← Aplicación principal (Django)
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env / .env.example
│   ├── db.sqlite3
│   │
│   ├── config/                           ← Configuración del proyecto
│   │   ├── settings.py                   ← Carga .env, EMAIL_*, PAYPAL_*, MICROSERVICIO_*_URL, INSTALLED_APPS
│   │   ├── urls.py                       ← Login por rol, password_reset por usuario, todas las apps
│   │   ├── wsgi.py / asgi.py
│   │
│   ├── billing/                          ← App de Ventas (módulo principal)
│   │   ├── models.py                     ← Brand, ProductGroup, Supplier, Product, Customer,
│   │   │                                    Invoice (estado, tipo_pago, saldo, estado_cobro,
│   │   │                                    payment_method, paypal_order_id), InvoiceDetail, CreditNote
│   │   ├── views.py                      ← FBV (facturas, PDF) + CBV (resto), restringidas por rol
│   │   ├── services.py                   ← check_stock(), emit_invoice() (Contado/Crédito; dispara
│   │   │                                    factura electrónica), recalc_invoice()
│   │   ├── pdf.py                        ← build_invoice_pdf(): genera el PDF de una factura
│   │   ├── forms.py, ProductForm.py, CustomerForm.py
│   │   ├── urls.py, admin.py, tests.py, migrations/
│   │   └── templates/billing/
│   │
│   ├── purchasing/                       ← App de Compras (solo Administrador / Analista de Compras)
│   │   ├── models.py                     ← Purchase (estado, tipo_pago, saldo, estado_pago),
│   │   │                                    PurchaseDetail, SupplierCreditNote
│   │   ├── views.py, forms.py, urls.py, admin.py, migrations/
│   │   └── templates/purchasing/
│   │
│   ├── inventory/                        ← App de Inventario (solo modelos y admin)
│   │   ├── models.py                     ← StockMovement (auditoría de movimientos)
│   │   └── admin.py, migrations/
│   │
│   ├── creditoventa/                     ← Cuentas por Cobrar: abonos sobre facturas a crédito
│   │   ├── models.py                     ← CobroFactura, registrar_cobro()/actualizar_cobro()/
│   │   │                                    eliminar_cobro() (recalculan saldo/estado_cobro)
│   │   ├── views.py                      ← Lista de facturas a crédito, registrar/editar/eliminar
│   │   │                                    abonos, historial de pagos; notifica al microservicio de pagos
│   │   └── forms.py, urls.py, admin.py, tests.py, migrations/, templates/creditoventa/
│   │
│   ├── pagos/                            ← Cuentas por Pagar: abonos sobre compras a crédito
│   │   ├── models.py                     ← PagoCompra, registrar_pago()/actualizar_pago()/
│   │   │                                    eliminar_pago() (recalculan saldo/estado_pago)
│   │   ├── views.py                      ← Lista de compras a crédito, registrar/editar/eliminar
│   │   │                                    abonos, historial de pagos
│   │   └── forms.py, urls.py, admin.py, tests.py, migrations/, templates/pagos/
│   │
│   ├── security/                         ← App de Seguridad: usuarios, roles y permisos
│   │   ├── views.py                      ← RoleSelectLoginView, RoleLoginView,
│   │   │                                    UsernamePasswordResetView, CRUD de Usuarios/Roles/Permisos
│   │   ├── management/commands/setup_roles.py  ← Crea/actualiza los 4 roles y sus permisos
│   │   ├── templatetags/security_tags.py       ← Filtros {{ user|has_group:'X' }}
│   │   └── forms.py, urls.py, templates/security/
│   │
│   ├── store/                            ← App de Tienda (rol Cliente)
│   │   ├── models.py                     ← Cart (OneToOne → Customer), CartItem
│   │   ├── views.py                      ← Registro, catálogo, carrito, checkout, endpoints
│   │   │                                    AJAX de PayPal; notifica a ambos microservicios
│   │   ├── paypal.py                     ← Wrapper del REST API v2 de PayPal
│   │   └── forms.py, urls.py, admin.py, migrations/, templates/store/
│   │
│   ├── shared/                           ← Código reutilizable (no es una app Django)
│   │   ├── mixins.py                     ← SearchListMixin, ExportMixin, GroupRequiredMixin,
│   │   │                                    AdminOnlyMixin, ClienteRequiredMixin
│   │   ├── money.py                      ← round_money() con ROUND_HALF_UP
│   │   ├── decorators.py                 ← @audit_action, roles_required(), user_has_role(), @cliente_required
│   │   ├── emails.py                     ← send_welcome_email(), send_invoice_email()
│   │   ├── microservicios.py             ← Cliente HTTP hacia microservicio_pagos y microservicio_facturacion
│   │   └── validators.py                 ← validate_cedula_ec, validate_only_letters, validate_phone_ec
│   │
│   └── templates/registration/           ← Login, signup, cambio/recuperación de contraseña
│
├── microservicio_pagos/                  ← Microservicio de Pagos (FastAPI, independiente)
│   ├── main.py                           ← POST /api/pagos, POST /api/abonos, GET /health
│   ├── requirements.txt
│   └── .env / .env.example
│
└── microservicio_facturacion/            ← Microservicio de Facturación Electrónica (FastAPI, independiente)
    ├── main.py                           ← POST /api/facturar, GET /health
    ├── requirements.txt
    └── .env / .env.example
```

> `Supplier` y `Product` son compartidos entre apps de Django; `purchasing`, `inventory`, `store`, `creditoventa` y `pagos` los importan de `billing.models`.

### Nota sobre nombres parecidos: app `pagos` vs. `microservicio_pagos`

Dentro de `ProyectoDjango/` existe la app `pagos`, que es **Cuentas por Pagar** (abonos a proveedores sobre compras a crédito) — vive en la base de datos de Django. Aparte, en la raíz del repositorio existe `microservicio_pagos/`, un servicio **FastAPI independiente** que simula el procesamiento de un pago (tarjeta/PayPal) y envía correos de confirmación de pago/abono. Son dos cosas distintas que comparten nombre por el dominio (ambas hablan de "pagos"), no por relación de código.

---

## Modelos y Relaciones

### App `billing` (Ventas)

| Modelo          | Relaciones y notas                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------------------|
| `Brand`         | —                                                                                                          |
| `ProductGroup`  | —                                                                                                          |
| `Supplier`      | Campo `photo` (ImageField)                                                                                 |
| `Product`       | FK → Brand, FK → ProductGroup, M2M → Supplier. Campos: `photo`, `tax_rate`, `stock`, `is_active`          |
| `Customer`      | Campo `photo`. **`user`**: OneToOne opcional → `auth.User` (vincula la cuenta de un Cliente autoregistrado con su ficha de facturación). `first_name`/`last_name` validan solo letras (`validate_only_letters`), `phone` valida formato ecuatoriano (`validate_phone_ec`) |
| `Invoice`       | FK → Customer. `estado`: Borrador(0) / Emitida(1) / Anulada(2). **`tipo_pago`** ('contado'/'credito'), **`saldo`** y **`estado_cobro`** ('PENDIENTE'/'PAGADA') gestionan la venta a crédito junto con `creditoventa.CobroFactura`. **`payment_method`** ('card'/'paypal') y **`paypal_order_id`**: solo se llenan cuando la factura nace de un checkout online. Al emitirse dispara el envío de la factura electrónica al correo del cliente y la notificación al microservicio de Facturación |
| `InvoiceDetail` | FK → Invoice, FK → Product. Campo `discount_pct` (0-100). `quantity` con `MinValueValidator(1)`: no admite cantidades en cero o negativas |
| `CreditNote`    | FK → Invoice. Tipos: Devolución Total / Parcial. `amount` > 0 y no puede superar el saldo disponible de la factura (total menos notas previas); `reason` exige mínimo 5 caracteres |

### App `purchasing` (Compras)

| Modelo               | Relaciones y notas                                                 |
|----------------------|--------------------------------------------------------------------|
| `Purchase`           | FK → Supplier. `estado`: Borrador / Confirmada / Anulada. **`tipo_pago`**, **`saldo`** y **`estado_pago`** gestionan la compra a crédito junto con `pagos.PagoCompra` |
| `PurchaseDetail`     | FK → Purchase (CASCADE), FK → Product (PROTECT). `quantity` con `MinValueValidator(1)` |
| `SupplierCreditNote` | FK → Purchase. Nota de crédito emitida por el proveedor. `amount` > 0 y no puede superar el saldo disponible de la compra; `reason` exige mínimo 5 caracteres |

### App `inventory` (Inventario)

| Modelo          | Relaciones y notas                                                              |
|-----------------|-----------------------------------------------------------------------------------|
| `StockMovement` | FK → Product, FK opcional → Invoice, FK opcional → Purchase, FK opcional → User    |

### App `creditoventa` (Cuentas por Cobrar)

| Modelo         | Relaciones y notas                                                                                     |
|----------------|-----------------------------------------------------------------------------------------------------------|
| `CobroFactura` | FK → `billing.Invoice` (`related_name='cobros'`). `valor` > 0. Cada creación/edición/eliminación recalcula `Invoice.saldo` y `Invoice.estado_cobro` desde cero (SUM de abonos), nunca de forma incremental |

### App `pagos` (Cuentas por Pagar)

| Modelo        | Relaciones y notas                                                                                     |
|---------------|-----------------------------------------------------------------------------------------------------------|
| `PagoCompra`  | FK → `purchasing.Purchase` (`related_name='pagos'`). `valor` > 0. Cada creación/edición/eliminación recalcula `Purchase.saldo` y `Purchase.estado_pago` desde cero (SUM de abonos), nunca de forma incremental |

### App `store` (Tienda del Cliente)

| Modelo     | Relaciones y notas                                                                 |
|------------|--------------------------------------------------------------------------------------|
| `Cart`     | OneToOne → `billing.Customer`. Propiedades `subtotal`, `tax`, `total`, `items_count` |
| `CartItem` | FK → Cart (CASCADE), FK → Product. `unique_together = (cart, product)`              |

> El checkout **no crea un modelo de "Pedido" aparte**: al capturar el pago se genera directamente un `Invoice` + `InvoiceDetail` (mismo ciclo de vida Borrador → Emitida que usa Ventas), reutilizando `billing/services.py` para descontar stock y registrar `StockMovement`, y notificando a los dos microservicios (pago aprobado + facturación electrónica).

---

## Funcionalidades del Sistema

### Módulo de Ventas

| Sección      | Operaciones                                                                        |
|--------------|--------------------------------------------------------------------------------------|
| Marcas       | Listar, Crear, Editar, Ver detalle, Exportar PDF/Excel — Eliminar solo Administrador |
| Grupos       | Listar, Crear, Editar, Ver detalle, Exportar PDF/Excel — Eliminar solo Administrador |
| Proveedores  | Listar, Crear, Editar, Eliminar, Ver detalle, Exportar — control total para Administrador y Analista de Compras |
| Productos    | Listar (con foto), Crear, Editar (balance dinámico), Ver detalle, Exportar — Eliminar solo Administrador; Vendedor solo puede ver |
| Clientes     | Listar (con foto), Crear, Editar (preview en vivo), Ver detalle, Exportar — Eliminar solo Administrador/Staff |
| Facturas     | Listar, Crear borrador, Emitir a Contado o Crédito, Ver detalle, Sustituir, Nota de Crédito, PDF, Exportar — Crear/Editar solo Administrador y Vendedor; Anular solo Administrador y Analista de Compras |

#### Ciclo de vida de facturas

```
Nueva Factura ──► Borrador ──► Emitir (Contado/Crédito) ──► Emitida ──► Anular ──► Anulada
                    │                        │
                  Editar                   Sustituir → nuevo Borrador
                  Eliminar                 Nota de Crédito
                                            Cobros (si es a Crédito, vía creditoventa)
```

- **Borrador** — se puede editar y eliminar; el stock **no** se modifica.
- **Emitida** — el stock se descuenta automáticamente al emitir. Si se emite **a Contado**, la factura queda saldada de inmediato (`saldo=0`, `estado_cobro=PAGADA`). Si se emite **a Crédito**, queda con `saldo=total` y `estado_cobro=PENDIENTE`, gestionable desde el módulo **Cuentas por Cobrar** (`creditoventa`). Se envía automáticamente la **factura electrónica** por correo al cliente (PDF adjunto) y se notifica al `microservicio_facturacion` (clave de acceso SRI simulada + XML por correo).
- **Anulada** — el stock se revierte automáticamente; registro histórico visible e inactivo.
- **Nota de Crédito** — documento contable vinculado a la factura original (devolución parcial o total); el monto se valida contra el saldo disponible de la factura.
- **Sustitución** — anula la factura original y crea un nuevo borrador con los mismos datos para corregir y volver a emitir.
- La emisión (descuento de stock + `StockMovement` + envío de factura electrónica) vive en `billing/services.py::emit_invoice()`, compartida entre la emisión manual (Vendedor/Administrador) y el checkout online de la Tienda.

#### Facturación electrónica

Al emitirse una factura (`emit_invoice()`):

1. `shared/emails.py::send_invoice_email()` genera el PDF con `billing/pdf.py::build_invoice_pdf()` y lo envía por correo al cliente directamente desde Django (fallo silencioso: nunca revierte la emisión).
2. `shared/microservicios.py::notificar_facturacion()` llama por HTTP a `microservicio_facturacion` (`POST /api/facturar`), que simula la autorización SRI (clave de acceso de 49 dígitos con módulo 11, XML del comprobante) y envía un segundo correo con el XML adjunto. Si el microservicio está caído, solo se registra en el log — la factura ya quedó emitida en Django.

### Cuentas por Cobrar (`creditoventa`) y Cuentas por Pagar (`pagos`)

Ambos módulos siguen el mismo patrón: listado filtrable por estado (Pendiente/Pagada/Todas) + búsqueda, formulario de abono, historial de abonos, edición y eliminación (bloqueada si el documento ya está pagado en su totalidad). El saldo y el estado se **recalculan siempre desde cero** (`SUM` de abonos) dentro de una transacción con `select_for_update()`, para que nunca queden desincronizados.

| Módulo         | Documento base       | Quién lo usa                     | Notifica a                     |
|----------------|-----------------------|-----------------------------------|----------------------------------|
| `creditoventa` | `billing.Invoice` a Crédito     | Administrador, Vendedor           | `microservicio_pagos` (`/api/abonos`) — correo de confirmación de abono al cliente |
| `pagos`        | `purchasing.Purchase` a Crédito | Administrador, Analista de Compras | *(no notifica a un microservicio; es interno)* |

### Módulo de Compras

Acceso exclusivo de **Administrador** y **Analista de Compras** (bloqueado a nivel de servidor, no solo oculto en el menú).

| Sección            | Operaciones                                                                         |
|--------------------|---------------------------------------------------------------------------------------|
| Compras            | Listar, Crear borrador, Confirmar a Contado o Crédito, Anular, Ver detalle, Descargar PDF, Exportar |
| Nota de crédito    | Registrar nota de crédito del proveedor vinculada a la compra                       |
| Pagos a proveedor  | Registrar abonos sobre compras a crédito (módulo `pagos`), con historial            |

#### Ciclo de vida de compras

```
Nueva Compra ──► Borrador ──► Confirmar (Contado/Crédito) ──► Confirmada ──► Anular ──► Anulada
                   │                                              │
                 Eliminar                                    Pagos (si es a Crédito)
```

- **Borrador** — editable; stock no modificado.
- **Confirmada** — stock incrementado automáticamente con `F()` + `atomic()`; registra `StockMovement`. A Contado queda saldada de inmediato; a Crédito genera saldo pendiente gestionable desde `pagos`.
- **Anulada** — stock revertido; registra `StockMovement`.

### Módulo de Seguridad (Administrador)

| Sección              | Descripción                                                                                     |
|----------------------|------------------------------------------------------------------------------------------------------|
| Usuarios             | Listar, editar datos y roles, eliminar. Alta de nuevas cuentas (`+ Nuevo Usuario`) con cualquier rol — envía correo de bienvenida con usuario, contraseña y rol asignado |
| Roles                | Crear/editar/eliminar roles (`Group`) y sus permisos con checkboxes                              |
| Permisos             | Crear/editar/eliminar permisos personalizados + **matriz de permisos por rol**: cada fila es un permiso, cada columna un rol, con checkbox por celda y un checkbox "marcar/desmarcar todos" por rol |
| Login por rol        | `/accounts/login/` muestra una tarjeta por rol; cada tarjeta lleva a un login anclado a ese rol (rechaza credenciales válidas si la cuenta no tiene ese rol) |
| Recuperar contraseña | El usuario ingresa su **nombre de usuario**; si existe, se envía un correo (a la dirección ya registrada) con un enlace único para elegir una nueva contraseña. Funciona para cuentas autoregistradas y para las creadas por el Administrador |

### Tienda en línea (Cliente)

| Sección           | Descripción                                                                                          |
|-------------------|------------------------------------------------------------------------------------------------------------|
| Registro público  | Formulario en la página de inicio (`/tienda/registro/`): crea la cuenta con rol Cliente, la vincula a un `Customer` y envía el correo de bienvenida. Inicia sesión automáticamente |
| Catálogo          | Solo productos activos; sin columnas de balance/estado; barra de búsqueda (nombre/descripción/marca) y sidebar de categorías; botón "Añadir al carrito" (deshabilitado si no hay stock) |
| Carrito           | Cantidad editable por línea (limitada al stock disponible), quitar producto, subtotal/IVA/total |
| Checkout          | Botones reales de **PayPal** y de **Tarjeta de débito/crédito** (PayPal Checkout con `enable-funding=card`, mismo SDK) |
| Confirmación      | Al capturar el pago se genera la factura (Contado), se descuenta el stock, se vacía el carrito, se envía la factura electrónica al correo del cliente y se notifica a `microservicio_pagos` (correo de pago aprobado) y a `microservicio_facturacion` (correo con la clave SRI simulada) |

---

## Arquitectura de Microservicios

```
┌─────────────────────────┐        HTTP (requests, fail-silent)
│   ProyectoDjango/        │ ───────────────────────────────────┐
│   (Django, puerto 8000)  │                                     │
│   shared/microservicios.py│                                    │
└─────────────┬────────────┘                                     │
              │                                                   │
              │ POST /api/pagos, /api/abonos           POST /api/facturar
              ▼                                                   ▼
┌─────────────────────────┐                       ┌────────────────────────────┐
│  microservicio_pagos     │                       │  microservicio_facturacion  │
│  FastAPI, puerto 5001    │                       │  FastAPI, puerto 5002       │
│  Simula Sandbox de pago  │                       │  Simula autorización SRI    │
│  Envía correo (SMTP)     │                       │  Envía correo con XML (SMTP)│
└─────────────────────────┘                       └────────────────────────────┘
```

- Ninguno de los dos microservicios tiene base de datos propia ni conoce los modelos de Django: reciben un JSON, responden un JSON, y opcionalmente envían un correo por `smtplib`.
- Django los llama **después** de confirmar la operación en su propia base de datos (venta ya emitida, abono ya registrado). Si un microservicio está apagado o falla, la excepción se atrapa y se registra en el log — la operación en Django **ya quedó confirmada** y no se revierte.
- Cada microservicio expone `GET /health` para verificar que está arriba, y documentación interactiva automática de FastAPI en `/docs` (Swagger UI).
- Las URLs base se configuran en `ProyectoDjango/.env` (`MICROSERVICIO_PAGOS_URL`, `MICROSERVICIO_FACTURACION_URL`) — por defecto apuntan a `127.0.0.1:5001` y `127.0.0.1:5002`.

---

## Configuración de variables de entorno

Cada uno de los tres proyectos tiene su propio `.env.example`. Cópialo como `.env` en la misma carpeta y completa los valores.

### `ProyectoDjango/.env`

```dotenv
# Email (si se deja vacío, se usa el backend de consola: los correos se
# imprimen en la terminal en vez de enviarse de verdad — útil en desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=TecnoStock <noreply@tecnostock.ec>

# PayPal (crear una app en https://developer.paypal.com/ -> Sandbox -> Apps)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox

# Microservicios externos (FastAPI, independientes — ver /microservicio_pagos
# y /microservicio_facturacion junto a este proyecto)
MICROSERVICIO_PAGOS_URL=http://127.0.0.1:5001
MICROSERVICIO_FACTURACION_URL=http://127.0.0.1:5002
```

### `microservicio_pagos/.env`

```dotenv
# Puedes usar los MISMOS valores SMTP que ya tienes en ProyectoDjango/.env
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=TecnoStock Pagos <noreply@tecnostock.ec>
```

### `microservicio_facturacion/.env`

```dotenv
# Puedes usar los MISMOS valores SMTP que ya tienes en ProyectoDjango/.env
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=TecnoStock Facturación <noreply@tecnostock.ec>

# RUC del emisor, usado para simular la clave de acceso del SRI
RUC_EMISOR=0999999999001
```

> Para Gmail, `EMAIL_HOST_PASSWORD` debe ser una **contraseña de aplicación** (requiere verificación en 2 pasos activada), no la contraseña normal de la cuenta. Con `EMAIL_HOST` vacío/no configurado, los tres proyectos imprimen los correos en su propia terminal en vez de enviarlos — así puedes probar todo el flujo (venta, pago, factura electrónica, abono) sin credenciales SMTP reales.

---

## Ejecución del Proyecto

El sistema son **tres procesos independientes** que deben correr al mismo tiempo, cada uno en su propia terminal y con su propio entorno virtual: Django (puerto 8000) y los dos microservicios FastAPI (puertos 5001 y 5002). Los microservicios son opcionales para navegar el sistema, pero **se necesitan para** que el checkout de la Tienda y el módulo de Cobros disparen sus notificaciones por correo (si están apagados, Django sigue funcionando con normalidad — solo se registra un aviso en el log).

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ProyectoFinalDjango
```

### 2. Aplicación principal — `ProyectoDjango/`

```bash
cd ProyectoDjango

# Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env         # Windows
cp .env.example .env           # Mac / Linux
# Completa .env con tus credenciales SMTP y de PayPal Sandbox (ver sección anterior)

# Aplicar migraciones
python manage.py migrate

# Crear los roles del sistema (Administrador, Vendedor, Analista de Compras, Cliente)
python manage.py setup_roles

# Crear superusuario
python manage.py createsuperuser

# Iniciar el servidor de desarrollo
python manage.py runserver
```

Abrir el navegador en `http://127.0.0.1:8000`. El registro público de Clientes está en `http://127.0.0.1:8000/tienda/registro/` (enlazado desde la landing page).

### 3. Microservicio de Pagos — `microservicio_pagos/`

En una **segunda terminal**, desde la raíz del repositorio:

```bash
cd microservicio_pagos

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

pip install -r requirements.txt

copy .env.example .env         # Windows
cp .env.example .env           # Mac / Linux
# Completa .env (puedes reutilizar los mismos datos SMTP de ProyectoDjango/.env)

uvicorn main:app --reload --port 5001
```

Health check: `http://127.0.0.1:5001/health`. Documentación interactiva: `http://127.0.0.1:5001/docs`.

### 4. Microservicio de Facturación Electrónica — `microservicio_facturacion/`

En una **tercera terminal**, desde la raíz del repositorio:

```bash
cd microservicio_facturacion

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

pip install -r requirements.txt

copy .env.example .env         # Windows
cp .env.example .env           # Mac / Linux
# Completa .env (puedes reutilizar los mismos datos SMTP de ProyectoDjango/.env)

uvicorn main:app --reload --port 5002
```

Health check: `http://127.0.0.1:5002/health`. Documentación interactiva: `http://127.0.0.1:5002/docs`.

### 5. Probar el flujo completo

Con los tres servicios corriendo:

1. Entra como Administrador o Vendedor, crea un cliente con correo válido y una factura en Borrador.
2. Emítela eligiendo **Contado** o **Crédito**. Revisa la terminal de Django (correo de factura con PDF) y la de `microservicio_facturacion` (correo con la clave de acceso SRI simulada y el XML), o tu bandeja de entrada real si configuraste SMTP.
3. Si la emitiste a Crédito, ve a **Cuentas por Cobrar** y registra un abono: revisa la terminal de `microservicio_pagos` (correo de confirmación de abono).
4. Como Cliente, agrega productos al carrito en la Tienda y paga con PayPal Sandbox o Tarjeta: revisa las terminales de ambos microservicios.

Si no configuraste credenciales SMTP reales en ninguno de los tres `.env`, todos los correos se imprimen en su terminal correspondiente en vez de enviarse — el flujo funciona igual de principio a fin.

---

## Dependencias principales

### `ProyectoDjango/requirements.txt`

```
Django==6.0.6
django-extensions==4.1
reportlab==4.5.1
openpyxl==3.1.5
pillow==12.2.0
python-dotenv==1.2.2
requests==2.34.2
```

### `microservicio_pagos/requirements.txt` y `microservicio_facturacion/requirements.txt`

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic[email]==2.10.4
python-dotenv==1.0.1
```

> No se necesita instalar nada adicional; todas las dependencias ya están declaradas en el `requirements.txt` de cada carpeta.

---

## Características Transversales

| Característica            | Descripción                                                                          |
|---------------------------|--------------------------------------------------------------------------------------|
| Autenticación por rol      | Login con tarjetas de rol; cada rol solo entra por su propia tarjeta               |
| Recuperación de contraseña | Por nombre de usuario, con correo real vía SMTP                                     |
| Correo transaccional       | Bienvenida, recuperación de contraseña, factura electrónica (PDF, desde Django), autorización SRI simulada (XML, desde `microservicio_facturacion`), confirmación de pago y de abonos (desde `microservicio_pagos`) |
| Ventas y compras a crédito | `Invoice`/`Purchase` con `tipo_pago`, `saldo` y `estado_cobro`/`estado_pago`; abonos gestionados por `creditoventa` y `pagos` con recálculo atómico del saldo |
| Control de permisos        | `GroupRequiredMixin` / `AdminOnlyMixin` / `ClienteRequiredMixin` / `roles_required()` protegen cada vista en el servidor, no solo el menú |
| Matriz de permisos         | Asignar/quitar permisos de todos los roles desde una sola pantalla                   |
| Pago real en línea         | PayPal Checkout (sandbox) con dos opciones: cuenta PayPal o tarjeta                  |
| Microservicios desacoplados| Pagos y Facturación Electrónica como servicios FastAPI independientes, comunicados por HTTP con fallo silencioso |
| Auditoría de stock         | `StockMovement` registra cada entrada/salida con tipo, usuario, fecha y documento    |
| Búsqueda y filtros         | Buscador por múltiples campos + filtros por fecha, estado, rango de precios/categoría |
| Paginación                 | Paginación automática en todos los listados                                         |
| Exportación                | Botones PDF y Excel en los módulos administrativos                                  |
| PDF de documentos          | Facturas y compras exportables a PDF con ReportLab                                  |
| Modal de detalle           | Botón "Ver" abre modal con foto/avatar, datos del registro y botón Editar integrado |
| Mostrar/ocultar contraseña | Registro, login y cambio/recuperación de contraseña                                 |
| Modo oscuro / claro        | Toggle en la barra de navegación; preferencia guardada en `localStorage`             |
| Validación de cédula       | Validador `validate_cedula_ec` con algoritmo oficial del Registro Civil del Ecuador  |
| Validaciones de negocio    | Nombres solo letras, teléfono ecuatoriano, precios/montos > 0, cantidades ≥ 1, motivos con longitud mínima, y monto de abonos/notas de crédito limitado al saldo disponible |
| Landing page pública       | Página de inicio de TecnoStock S.A. sin requerir login                              |
| Dashboard con KPIs         | Ventas/compras/margen bruto, gráficos Chart.js, top 5 productos y proveedores (Cliente es redirigido a la tienda en vez de ver este panel) |

---

## Carpeta `shared/` — Código Reutilizable (Django)

### `SearchListMixin` / `ExportMixin` / `SearchExportMixin`
Búsqueda declarativa + paginación + exportación PDF/Excel para cualquier `ListView` (usado también por el catálogo de la Tienda).

### `StaffRequiredMixin`
Protege vistas de eliminación heredadas del esquema anterior: solo `is_staff = True`.

### `GroupRequiredMixin` / `AdminOnlyMixin` / `ClienteRequiredMixin`
Restringen vistas por rol (`Group`). `AdminOnlyMixin` exige el rol Administrador sin excepciones; `ClienteRequiredMixin` exige el rol Cliente; `GroupRequiredMixin` es la base configurable (`group_required`, `strict`) que usan las vistas de Marcas/Grupos/Proveedores/Productos/Compras.

### `roles_required()` / `user_has_role()` / `cliente_required` (decoradores)
`roles_required()` y `cliente_required` protegen vistas de función completas; `user_has_role()` es un chequeo puntual dentro de una vista (por ejemplo, para decidir si se notifica a un microservicio sin bloquear toda la vista).

### `@audit_action`
Decorador que registra en el logger `audit` cada acción importante: usuario, acción, IP, método HTTP y timestamp.

### `send_welcome_email()` / `send_invoice_email()`
Correo de bienvenida (usuario/contraseña/rol) y factura electrónica (PDF adjunto, generado con `billing/pdf.py::build_invoice_pdf()`) enviados directamente por Django vía SMTP.

### `microservicios.py` — `notificar_pago()` / `notificar_abono()` / `notificar_facturacion()`
Cliente HTTP delgado hacia `microservicio_pagos` y `microservicio_facturacion`. Todas las funciones fallan en silencio (solo loguean la excepción): un microservicio caído nunca revierte una venta, emisión de factura o abono ya confirmados en la BD local de Django.

### `validate_cedula_ec` / `validate_only_letters` / `validate_phone_ec`
`validate_cedula_ec` valida que el campo `dni` sea matemáticamente correcto según el algoritmo del Registro Civil del Ecuador. `validate_only_letters` exige que el campo contenga solo letras (con tildes y Ñ, espacios o guiones entre palabras) — usado en nombres/apellidos de `Customer`, `Supplier.contact_name` y en los formularios de registro de usuario. `validate_phone_ec` exige un teléfono ecuatoriano válido (convencional de 7-9 dígitos, celular de 10 dígitos, o formato `+593` + 9 dígitos) — usado en `Customer.phone` y `Supplier.phone`.

---

## Uso de Inteligencia Artificial

Durante el desarrollo del proyecto se utilizó **Claude (Anthropic)** como herramienta de apoyo para:

- Revisar que el proyecto cumpliera los requisitos de la guía de la tarea
- Resolver dudas sobre relaciones entre modelos y el ORM de Django
- Orientación en la implementación de `inlineformset_factory` para facturas y compras con detalle
- Apoyo en la implementación de mixins reutilizables (`SearchExportMixin`)
- Implementación del ciclo de vida de facturas y compras (Borrador / Emitida-Confirmada / Anulada)
- Uso de expresiones `F()` para actualizaciones atómicas de stock
- Diseño del módulo de Compras y la landing page pública
- Diseño e implementación del sistema de roles (Cliente, Vendedor, Analista de Compras, Administrador) y su matriz de permisos
- Integración de correo transaccional (bienvenida y recuperación de contraseña) vía SMTP
- Implementación de la Tienda en línea: catálogo con búsqueda y categorías, carrito y checkout
- Integración real con PayPal Checkout (pago con cuenta PayPal o con tarjeta) mediante su API REST v2
- Implementación de la facturación electrónica: envío automático de la factura (PDF adjunto) al correo del cliente al emitirse, reutilizando el generador de PDF existente
- Diseño e implementación de la venta/compra a Contado o Crédito, con los módulos de Cuentas por Cobrar (`creditoventa`) y Cuentas por Pagar (`pagos`) y su recálculo atómico de saldo
- Diseño e implementación de los microservicios independientes `microservicio_pagos` y `microservicio_facturacion` (FastAPI) y su integración desacoplada (fallo silencioso) con Django
- Revisión y refuerzo de validaciones de negocio en todo el proyecto (formatos, campos obligatorios, rangos numéricos, fechas, montos contra saldos disponibles)
- Generación del `.gitignore` y este `README`

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
