                            CREATE
Sestencia
infinix = Brand.objects.create(name='Infinix', description='Electronics')
Resultado
INSERT INTO "billing_brand" ("name", "description", "is_active", "created_at", "updated_at")
VALUES ('Infinix', 'Electronics', 1, '2026-06-24 21:35:53.427132', '2026-06-24 21:35:53.428803') RETURNING "billing_brand"."id"

Sentencia
frutasyverduras = ProductGroup.objects.create(name='Frutas y Verduras')
Resultasdo
INSERT INTO "billing_productgroup" ("name", "is_active", "created_at", "updated_at")
VALUES ('Frutas y Verduras', 1, '2026-06-24 21:39:54.734808', '2026-06-24 21:39:54.734864') RETURNING "billing_productgroup"."id"

Sentencia
dist = Supplier.objects.create(name='Logitech', email='info@logitech.com')
Resultado
INSERT INTO "billing_supplier" ("name", "contact_name", "email", "phone", "address", "photo", "is_active", "created_at", "updated_at")
VALUES ('Logitech', NULL, 'info@logitech.com', NULL, NULL, '', 1, '2026-06-24 23:26:07.496163', '2026-06-24 23:26:07.497051') RETURNING "billing_supplier"."id"

Sentencia 
phone = Product.objects.create(name='Infinix GT 30 Pro', brand=infinix, group=electronics, unit_price=424.99, stock=80)
Resultado
INSERT INTO "billing_product" ("name", "description", "brand_id", "group_id", "photo", "unit_price", "tax_rate", "stock", "is_active", "created_at", "updated_at")
VALUES ('Infinix GT 30 Pro', NULL, 9, 1, '', '424.990000000', '0.15', 80, 1, '2026-06-24 23:36:53.718443', '2026-06-24 23:36:53.718617') RETURNING "billing_product"."id" (Observación, como ya tenía Electronics guardado en una sesion anterior me dió error porque en group=electronics electronics no estaba definido así que con get lo conseguí para poder realizar la acción.)

Sentencia
phone.suppliers.add(dist, global_s)
Resultado
INSERT
    OR
IGNORE INTO "billing_product_suppliers" ("product_id", "supplier_id")
VALUES (6, 2), (6, 5)

Sentencia
client = Customer.objects.create(dni='0953393584', first_name='Lando', last_name='Norris', email = "landinho@hottmail.com", phone='0999887766')
Resultado
INSERT INTO "billing_customer" ("dni", "first_name", "last_name", "email", "phone", "address", "photo", "is_active", "created_at", "updated_at")
VALUES ('0953393584', 'Lando', 'Norris', 'landinho@hottmail.com', '0999887766', NULL, '', 1, '2026-06-24 23:48:06.085875', '2026-06-24 23:48:06.087522') RETURNING "billing_customer"."id"


                    READ
Sentencia
Brand.objects.all()
Resultado
SELECT "billing_brand"."id", "billing_brand"."name", "billing_brand"."description", "billing_brand"."is_active", "billing_brand"."created_at", "billing_brand"."updated_at" FROM "billing_brand" ORDER BY "billing_brand"."name" ASC
<QuerySet [<Brand: Apple>, <Brand: DELL>, <Brand: Infinix>, <Brand: La Italiana>, <Brand: Lenovo>, <Brand: Nutri Leche>, <Brand: Samsung>]>

Sentencia
Brand.objects.get(name='Lenovo')
Resultado
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."name" = 'Lenovo'
 LIMIT 21
Execution time: 0.000946s [Database: default]
Out[19]: <Brand: Lenovo>

Sentencia
Product.objects.filter(unit_price__lt=500)
Resultado
Out[20]: SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 WHERE "billing_product"."unit_price" < '500'
 ORDER BY "billing_product"."name" ASC
 LIMIT 21

Execution time: 0.004017s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 9
 LIMIT 21

Execution time: 0.000345s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 6
 LIMIT 21

Execution time: 0.000258s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 8
 LIMIT 21

Execution time: 0.000188s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 1
 LIMIT 21

Execution time: 0.000206s [Database: default]
<QuerySet [<Product: Infinix GT 30 Pro (Infinix)>, <Product: Jamón de espalda (La Italiana)>, <Product: Mouse DELL (DELL)>, <Product: Teclado (Samsung)>]>


Sentencia
Product.objects.filter(unit_price__range=(100,500))
Resultado
Out[21]: SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 WHERE "billing_product"."unit_price" BETWEEN '100' AND '500'
 ORDER BY "billing_product"."name" ASC
 LIMIT 21

Execution time: 0.002188s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 9
 LIMIT 21
Execution time: 0.000245s [Database: default]
<QuerySet [<Product: Infinix GT 30 Pro (Infinix)>]>

Sentencia
Product.objects.filter(name__icontains='jam')
Resultado
Out[22]: SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 WHERE "billing_product"."name" LIKE '%jam%' ESCAPE '\'
 ORDER BY "billing_product"."name" ASC
 LIMIT 21
Execution time: 0.005860s [Database: default]
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = 6
 LIMIT 21
<QuerySet [<Product: Jamón de espalda (La Italiana)>]>

Sentencia
Product.objects.exclude(stock=0)
Resultado
SELECT "billing_product"."id", "billing_product"."name", "billing_product"."description", "billing_product"."brand_id", "billing_product"."group_id", "billing_product"."photo", "billing_product"."unit_price", "billing_product"."tax_rate", "billing_product"."stock", "billing_product"."is_active", "billing_product"."created_at", "billing_product"."updated_at" FROM "billing_product" WHERE NOT ("billing_product"."stock" = 0) ORDER BY "billing_product"."name" ASC
<QuerySet [<Product: Galaxy s24 (Samsung)>, <Product: Infinix GT 30 Pro (Infinix)>, <Product: Jamón de espalda (La Italiana)>, <Product: Lenovo Thinkbook 14 G6 Core I7 13700h Ssd 1tb Ram 32gb Plateado (Lenovo)>, <Product: Mouse DELL (DELL)>, <Product: Teclado (Samsung)>]>

Sentencia
Product.objects.order_by('-unit_price')
Resultado
SELECT "billing_product"."id", "billing_product"."name", "billing_product"."description", "billing_product"."brand_id", "billing_product"."group_id", "billing_product"."photo", "billing_product"."unit_price", "billing_product"."tax_rate", "billing_product"."stock", "billing_product"."is_active", "billing_product"."created_at", "billing_product"."updated_at" FROM "billing_product" ORDER BY "billing_product"."unit_price" DESC
<QuerySet [<Product: Lenovo Thinkbook 14 G6 Core I7 13700h Ssd 1tb Ram 32gb Plateado (Lenovo)>, <Product: Galaxy s24 (Samsung)>, <Product: Infinix GT 30 Pro (Infinix)>, <Product: Mouse DELL (DELL)>, <Product: Teclado (Samsung)>, <Product: Jamón de espalda (La Italiana)>]>

Sentencia
Product.objects.count()
Resultado
SELECT COUNT(*) AS "__count"
  FROM "billing_product"
Execution time: 0.002462s [Database: default]
Out[25]: 6

Sentencia
Product.objects.filter(stock=0).exists()
Resultado
SELECT 1 AS "a"
  FROM "billing_product"
 WHERE "billing_product"."stock" = 0
 LIMIT 1
Execution time: 0.000499s [Database: default]
Out[26]: False



                      UPDATE

Sentencia
b = Brand.objects.get(name='Samsung'); b.description = 'Updated'; b.save()
Resultado
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."name" = 'Samsung'
 LIMIT 21

UPDATE "billing_brand"
   SET "name" = 'Samsung',
       "description" = 'Updated',
       "is_active" = 1,
       "updated_at" = '2026-06-24 ...'
 WHERE "billing_brand"."id" = 1

Sentencia
Product.objects.filter(stock=0).update(is_active=False) 
Resultado
UPDATE "billing_product"
   SET "is_active" = 0
 WHERE "billing_product"."stock" = 0

Sentencia
p = Product.objects.get(name='Galaxy S24')
Resultado
SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 WHERE "billing_product"."name" = 'Galaxy S24'
 LIMIT 21

Sentencia
p.suppliers.add(global_s) # M2M: agregar
Resultado
INSERT
    OR
IGNORE INTO "billing_product_suppliers" ("product_id", "supplier_id")
VALUES (X, Y)

Sentencia
p.suppliers.remove(global_s) # M2M: quitar
Resultado
DELETE FROM "billing_product_suppliers"
 WHERE ("billing_product_suppliers"."product_id" = X
   AND "billing_product_suppliers"."supplier_id" IN (Y))

Sentencia
p.suppliers.clear() # M2M: quitar todos
Resultado
DELETE FROM "billing_product_suppliers"
 WHERE "billing_product_suppliers"."product_id" IN (X)

Sentencia
p.suppliers.set([dist]) # M2M: reemplazar
Resultado
SELECT "billing_product_suppliers"."supplier_id"
  FROM "billing_product_suppliers"
 WHERE "billing_product_suppliers"."product_id" = X

DELETE FROM "billing_product_suppliers"
 WHERE ("billing_product_suppliers"."product_id" = X
   AND "billing_product_suppliers"."supplier_id" IN (Y))

INSERT
    OR
IGNORE INTO "billing_product_suppliers" ("product_id", "supplier_id")
VALUES (X, Z)

Sentencia
c = Customer.objects.get(dni='0912345678')
Resultado
SELECT "billing_customer"."id",
       "billing_customer"."dni",
       "billing_customer"."first_name",
       "billing_customer"."last_name",
       "billing_customer"."email",
       "billing_customer"."phone",
       "billing_customer"."address",
       "billing_customer"."photo",
       "billing_customer"."is_active",
       "billing_customer"."created_at",
       "billing_customer"."updated_at"
  FROM "billing_customer"
 WHERE "billing_customer"."dni" = '0912345678'
 LIMIT 21

Sentencia
c.profile.credit_limit = 10000; c.profile.save() # OneToOne
Resultado
SELECT "billing_customerprofile"."id",
       "billing_customerprofile"."customer_id",
       "billing_customerprofile"."taxpayer_type",
       "billing_customerprofile"."payment_terms",
       "billing_customerprofile"."credit_limit",
       "billing_customerprofile"."notes"
  FROM "billing_customerprofile"
 WHERE "billing_customerprofile"."customer_id" = X
 LIMIT 21

UPDATE "billing_customerprofile"
   SET "customer_id" = X,
       "taxpayer_type" = 'final',
       "payment_terms" = 'cash',
       "credit_limit" = '10000.00',
       "notes" = NULL
 WHERE "billing_customerprofile"."id" = Y

Sentencia
from django.db.models import F
Product.objects.update(unit_price=F('unit_price') * 1.10) # F()
Resultado
UPDATE "billing_product"
   SET "unit_price" = ("billing_product"."unit_price" * '1.1')



               RELACIONES

# FK
Sentencia
product.brand.name
Resultado
SELECT "billing_brand"."id",
       "billing_brand"."name",
       "billing_brand"."description",
       "billing_brand"."is_active",
       "billing_brand"."created_at",
       "billing_brand"."updated_at"
  FROM "billing_brand"
 WHERE "billing_brand"."id" = X
 LIMIT 21

Sentencia
samsung.products.all()
Resultado
SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 WHERE "billing_product"."brand_id" = X
 ORDER BY "billing_product"."name" ASC

# M2M
Sentencia
product.suppliers.all()
Resultado
SELECT "billing_supplier"."id",
       "billing_supplier"."name",
       "billing_supplier"."contact_name",
       "billing_supplier"."email",
       "billing_supplier"."phone",
       "billing_supplier"."address",
       "billing_supplier"."photo",
       "billing_supplier"."is_active",
       "billing_supplier"."created_at",
       "billing_supplier"."updated_at"
  FROM "billing_supplier"
 INNER JOIN "billing_product_suppliers" ON ("billing_supplier"."id" = "billing_product_suppliers"."supplier_id")
 WHERE "billing_product_suppliers"."product_id" = X
 ORDER BY "billing_supplier"."name" ASC

Sentencia
supplier.products.all()
Resultado
SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 INNER JOIN "billing_product_suppliers" ON ("billing_product"."id" = "billing_product_suppliers"."product_id")
 WHERE "billing_product_suppliers"."supplier_id" = X
 ORDER BY "billing_product"."name" ASC

Sentencia
Product.objects.filter(suppliers__name='TechDist')
Resultado
SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 INNER JOIN "billing_product_suppliers" ON ("billing_product"."id" = "billing_product_suppliers"."product_id")
 INNER JOIN "billing_supplier" ON ("billing_product_suppliers"."supplier_id" = "billing_supplier"."id")
 WHERE "billing_supplier"."name" = 'TechDist'
 ORDER BY "billing_product"."name" ASC
<QuerySet [<Product: Galaxy s24 (Samsung)>, <Product: Lenovo Thinkbook 14 G6 Core I7 13700h Ssd 1tb Ram 32gb Plateado (Lenovo)>]>

# OneToOne
Sentencia
client.profile.credit_limit
Resultado
SELECT "billing_customerprofile"."id",
       "billing_customerprofile"."customer_id",
       "billing_customerprofile"."taxpayer_type",
       "billing_customerprofile"."payment_terms",
       "billing_customerprofile"."credit_limit",
       "billing_customerprofile"."notes"
  FROM "billing_customerprofile"
 WHERE "billing_customerprofile"."customer_id" = X
 LIMIT 21

Sentencia
profile.customer.full_name
Resultado
SELECT "billing_customer"."id",
       "billing_customer"."dni",
       "billing_customer"."first_name",
       "billing_customer"."last_name",
       "billing_customer"."email",
       "billing_customer"."phone",
       "billing_customer"."address",
       "billing_customer"."photo",
       "billing_customer"."is_active",
       "billing_customer"."created_at",
       "billing_customer"."updated_at"
  FROM "billing_customer"
 WHERE "billing_customer"."id" = X
 LIMIT 21

Sentencia
Customer.objects.filter(profile__taxpayer_type='ruc')
Resultado
SELECT "billing_customer"."id",
       "billing_customer"."dni",
       "billing_customer"."first_name",
       "billing_customer"."last_name",
       "billing_customer"."email",
       "billing_customer"."phone",
       "billing_customer"."address",
       "billing_customer"."photo",
       "billing_customer"."is_active",
       "billing_customer"."created_at",
       "billing_customer"."updated_at"
  FROM "billing_customer"
 INNER JOIN "billing_customerprofile" ON ("billing_customer"."id" = "billing_customerprofile"."customer_id")
 WHERE "billing_customerprofile"."taxpayer_type" = 'ruc'
 ORDER BY "billing_customer"."last_name" ASC,
          "billing_customer"."first_name" ASC
<QuerySet [<Customer: Perez, Juan>]>

# Q()
Sentencia
from django.db.models import Q
Product.objects.filter(Q(brand__name='Samsung') | Q(unit_price__gt=1000))
Resultado
SELECT "billing_product"."id",
       "billing_product"."name",
       "billing_product"."description",
       "billing_product"."brand_id",
       "billing_product"."group_id",
       "billing_product"."photo",
       "billing_product"."unit_price",
       "billing_product"."tax_rate",
       "billing_product"."stock",
       "billing_product"."is_active",
       "billing_product"."created_at",
       "billing_product"."updated_at"
  FROM "billing_product"
 INNER JOIN "billing_brand" ON ("billing_product"."brand_id" = "billing_brand"."id")
 WHERE ("billing_brand"."name" = 'Samsung' OR "billing_product"."unit_price" > '1000')
 ORDER BY "billing_product"."name" ASC
<QuerySet [<Product: Galaxy s24 (Samsung)>, <Product: Lenovo Thinkbook 14 G6 Core I7 13700h Ssd 1tb Ram 32gb Plateado (Lenovo)>, <Product: Teclado (Samsung)>]>

               AGREGACIONES

Sentencia
from django.db.models import Sum, Avg, Max, Min, Count
Product.objects.aggregate(avg=Avg('unit_price'))
Resultado
SELECT AVG("billing_product"."unit_price") AS "avg"
  FROM "billing_product"
{'avg': Decimal('450.580000000000')}

Sentencia
Product.objects.aggregate(max=Max('unit_price'), min=Min('unit_price'))
Resultado
SELECT MAX("billing_product"."unit_price") AS "max",
       MIN("billing_product"."unit_price") AS "min"
  FROM "billing_product"
{'max': Decimal('1200'), 'min': Decimal('8.5')}

Sentencia
Invoice.objects.filter(customer__dni='0912345678').aggregate(total=Sum('total'))
Resultado
SELECT SUM("billing_invoice"."total") AS "total"
  FROM "billing_invoice"
 INNER JOIN "billing_customer" ON ("billing_invoice"."customer_id" = "billing_customer"."id")
 WHERE "billing_customer"."dni" = '0912345678'
{'total': None}

Sentencia
Brand.objects.annotate(n=Count('products')).values('name', 'n')
Resultado
SELECT "billing_brand"."name",
       COUNT("billing_product"."id") AS "n"
  FROM "billing_brand"
  LEFT OUTER JOIN "billing_product" ON ("billing_product"."brand_id" = "billing_brand"."id")
 GROUP BY "billing_brand"."id",
          "billing_brand"."name"
 ORDER BY "billing_brand"."name" ASC
<QuerySet [{'name': 'Samsung', 'n': 2}, {'name': 'Apple', 'n': 0}, {'name': 'Nutri Leche', 'n': 0}, {'name': 'La Italiana', 'n': 1}, {'name': 'Lenovo', 'n': 1}, {'name': 'DELL', 'n': 1}, {'name': 'Infinix', 'n': 1}]>

Sentencia
Product.objects.annotate(ns=Count('suppliers')).values('name', 'ns')
Resultado
SELECT "billing_product"."name",
       COUNT("billing_product_suppliers"."supplier_id") AS "ns"
  FROM "billing_product"
  LEFT OUTER JOIN "billing_product_suppliers" ON ("billing_product_suppliers"."product_id" = "billing_product"."id")
 GROUP BY "billing_product"."id",
          "billing_product"."name"
 ORDER BY "billing_product"."name" ASC
<QuerySet [{'name': 'Galaxy s24', 'ns': 2}, {'name': 'Teclado', 'ns': 0}, {'name': 'Lenovo Thinkbook 14 G6 Core I7 13700h Ssd 1tb Ram 32gb Plateado', 'ns': 1}, {'name': 'Mouse DELL', 'ns': 1}, {'name': 'Infinix GT 30 Pro', 'ns': 2}, {'name': 'Jamón de espalda', 'ns': 1}]>


               ¿QUÉ HACE CADA SENTENCIA?

--- CREATE ---

Brand.objects.create(name='Infinix', description='Electronics')
  Inserta un nuevo registro en la tabla billing_brand y retorna el objeto creado.

ProductGroup.objects.create(name='Frutas y Verduras')
  Inserta un nuevo grupo/categoría de producto en billing_productgroup.

Supplier.objects.create(name='Logitech', email='info@logitech.com')
  Inserta un nuevo proveedor en billing_supplier con los campos indicados; los demás quedan en NULL.

Product.objects.create(name='Infinix GT 30 Pro', brand=infinix, group=electronics, unit_price=424.99, stock=80)
  Inserta un producto con FK a Brand y ProductGroup. Los objetos brand y group deben estar cargados en memoria previamente.

phone.suppliers.add(dist, global_s)
  Agrega dos proveedores al producto a través de la relación M2M. Genera INSERT OR IGNORE en la tabla intermedia billing_product_suppliers para cada proveedor.

Customer.objects.create(dni='0953393584', first_name='Lando', ...)
  Inserta un nuevo cliente en billing_customer con los datos proporcionados.

--- READ ---

Brand.objects.all()
  Retorna un QuerySet con todos los registros de Brand. Como el modelo tiene ordering = ['name'], aplica ORDER BY name ASC automáticamente.

Brand.objects.get(name='Lenovo')
  Busca y retorna un único objeto Brand con ese nombre exacto. Lanza DoesNotExist si no existe y MultipleObjectsReturned si hay más de uno.

Product.objects.filter(unit_price__lt=500)
  Retorna un QuerySet con los productos cuyo precio unitario sea menor a 500 (lookup __lt = less than).

Product.objects.filter(unit_price__range=(100,500))
  Retorna productos cuyo precio esté entre 100 y 500 inclusive. Se traduce a BETWEEN en SQL.

Product.objects.filter(name__icontains='jam')
  Retorna productos cuyo nombre contenga 'jam' sin importar mayúsculas/minúsculas (lookup __icontains). En SQLite usa LIKE con ESCAPE.

Product.objects.exclude(stock=0)
  Retorna todos los productos excepto los que tengan stock igual a 0. Es el inverso de filter(stock=0).

Product.objects.order_by('-unit_price')
  Retorna todos los productos ordenados por precio descendente. El signo - invierte el orden; sin él sería ASC.

Product.objects.count()
  Retorna un entero con el total de filas en billing_product. Genera SELECT COUNT(*) sin cargar objetos en memoria.

Product.objects.filter(stock=0).exists()
  Retorna True si existe al menos un producto con stock=0, False en caso contrario. Usa SELECT 1 ... LIMIT 1, más eficiente que count() o filter().

--- UPDATE ---

b = Brand.objects.get(name='Samsung'); b.description = 'Updated'; b.save()
  Carga el objeto en memoria (SELECT), modifica el atributo en Python y llama save() para sincronizar todos los campos con la BD (UPDATE completo de todos los campos, incluido updated_at).

Product.objects.filter(stock=0).update(is_active=False)
  Actualización masiva directa en la BD sin cargar objetos en Python. Genera un único UPDATE con WHERE. No dispara señales de Django ni actualiza updated_at.

p = Product.objects.get(name='Galaxy S24')
  Obtiene un único producto por nombre exacto para usarlo en las operaciones M2M siguientes.

p.suppliers.add(global_s)
  Agrega un proveedor a la relación M2M del producto. Si el vínculo ya existe, INSERT OR IGNORE lo ignora sin error.

p.suppliers.remove(global_s)
  Elimina un proveedor específico de la relación M2M del producto. Genera DELETE en billing_product_suppliers filtrando por product_id y supplier_id.

p.suppliers.clear()
  Elimina todos los proveedores asociados al producto de la tabla M2M. Genera DELETE filtrando solo por product_id.

p.suppliers.set([dist])
  Reemplaza la lista completa de proveedores. Internamente consulta los actuales (SELECT), borra los que no están en la nueva lista (DELETE) y agrega los nuevos (INSERT OR IGNORE).

c = Customer.objects.get(dni='0912345678')
  Obtiene un cliente por su número de DNI exacto.

c.profile.credit_limit = 10000; c.profile.save()
  Acceder a c.profile dispara un SELECT en billing_customerprofile (OneToOne). Modificar el atributo y llamar save() genera el UPDATE en ese registro.

Product.objects.update(unit_price=F('unit_price') * 1.10)
  Actualización masiva usando expresión F(). El cálculo ocurre dentro de la BD (no en Python), por lo que es eficiente y seguro ante condiciones de carrera. No actualiza updated_at al ser bulk update.

--- RELACIONES ---

product.brand.name
  Accede al objeto Brand relacionado por FK. Si no está cacheado (sin select_related), genera un SELECT adicional a billing_brand. El .name es acceso Python puro.

samsung.products.all()
  Usa el related_name='products' definido en la FK de Product hacia Brand para obtener todos los productos de esa marca con un SELECT con WHERE brand_id = X.

product.suppliers.all()
  Retorna todos los proveedores del producto haciendo INNER JOIN entre billing_supplier y la tabla intermedia billing_product_suppliers.

supplier.products.all()
  Relación M2M inversa: retorna todos los productos asociados a un proveedor usando INNER JOIN desde el lado del supplier.

Product.objects.filter(suppliers__name='TechDist')
  Filtra productos atravesando la relación M2M: hace doble INNER JOIN (product → product_suppliers → supplier) y filtra por el nombre del proveedor.

client.profile.credit_limit
  Acceder a client.profile dispara SELECT en billing_customerprofile WHERE customer_id = X (relación OneToOne). El .credit_limit es atributo Python del objeto cargado.

profile.customer.full_name
  Relación OneToOne inversa: acceder a profile.customer genera SELECT en billing_customer WHERE id = X. El .full_name es una @property Python, no un campo de BD.

Customer.objects.filter(profile__taxpayer_type='ruc')
  Filtra clientes atravesando la relación OneToOne hacia su perfil. Genera INNER JOIN entre billing_customer y billing_customerprofile.

Product.objects.filter(Q(brand__name='Samsung') | Q(unit_price__gt=1000))
  Usa Q() para combinar condiciones con OR. El primer Q requiere JOIN a billing_brand. Sin Q() no es posible expresar OR entre condiciones distintas.

--- AGREGACIONES ---

Product.objects.aggregate(avg=Avg('unit_price'))
  Calcula el promedio del precio de todos los productos. Retorna un dict {'avg': Decimal('...')}, no un QuerySet.

Product.objects.aggregate(max=Max('unit_price'), min=Min('unit_price'))
  Calcula máximo y mínimo en una sola query. Retorna dict con ambas claves. Más eficiente que dos aggregate() separados.

Invoice.objects.filter(customer__dni='0912345678').aggregate(total=Sum('total'))
  Suma el total de facturas de un cliente específico traversando la FK. Si no hay facturas, retorna {'total': None}.

Brand.objects.annotate(n=Count('products')).values('name', 'n')
  Anota cada marca con la cantidad de productos que tiene usando LEFT OUTER JOIN + GROUP BY. Las marcas sin productos aparecen con n=0. Retorna QuerySet de dicts.

Product.objects.annotate(ns=Count('suppliers')).values('name', 'ns')
  Anota cada producto con la cantidad de proveedores asociados usando LEFT OUTER JOIN a la tabla M2M + GROUP BY. Productos sin proveedores aparecen con ns=0.