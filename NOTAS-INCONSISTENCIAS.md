# Notas de inconsistencias en los enunciados

Autor: Juan David Sierra Orozco. Materia: Tópicos Especiales en Ingeniería de Software (EAFIT).

Este archivo lista todo lo que los enunciados de los tutoriales 1, 2 y 3 dicen de una forma y el código real necesita de otra. Cada punto tiene tres partes: qué decía el PDF, qué falló, qué hice. Las pruebas automáticas de `tienda_app/tests/` cubren cada arreglo.

## Tutorial 1

### 1.1 El repo base ya trae parte del resultado
- El PDF dice: clonar el repo del profesor y construir la Compra Rápida desde una FBV.
- Lo que encontré: el repo ya tiene `CompraView` y `CompraService` (con `ejecutar_compra`), el template `compra.html` y el gateway, y además mezcla ramas de tutoriales posteriores (Docker, Postgres).
- Qué hice: partí del commit del repo base donde solo existe la estructura de capas (antes de los tutoriales 2 y 3). La Compra Rápida del enunciado convive con lo que ya había: `CompraRapidaView` en `compra-rapida/<id>/` y `CompraRapidaService` en `services.py`. No toqué `CompraView` ni `CompraService` en este tutorial.

### 1.2 Nombres distintos entre tutoriales (vista y servicio)
- El PDF dice: T1 usa `CompraRapidaView` y `CompraRapidaService`; T2 y T3 usan `CompraView` y `CompraService`.
- Qué falló: si se copian los tres PDFs tal cual hay dos vistas y dos servicios que nunca se conectan entre sí.
- Qué hice: las dos parejas se quedan. `CompraRapidaView`/`CompraRapidaService` son el flujo de un clic del T1. `CompraView`/`CompraService` son el flujo del repo base, que T2 y T3 refactorizan. En el T2 las dos vistas pasan a usar la fábrica de pagos, así que el Mock funciona en ambas.

### 1.3 `CalculadorImpuestos.obtener_total_con_iva` no se define en el texto
- El PDF dice: el servicio llama a `CalculadorImpuestos.obtener_total_con_iva(libro.precio)` sin mostrar la clase ni los imports (`Libro`, `Inventario`, `CalculadorImpuestos`).
- Qué hice: la clase ya existe en `domain/logic.py` del repo base. Solo agregué los imports en `services.py`.

### 1.4 `Libro.objects.get` rompe con un id que no existe
- El PDF dice: `Libro.objects.get(id=libro_id)` y `Inventario.objects.get(libro=libro)`.
- Qué falló: un id inexistente lanza `DoesNotExist` y el usuario ve un error 500.
- Qué hice: uso `get_object_or_404` para el libro, igual que el resto de `services.py`, así que la respuesta es un 404 limpio. Un libro sin registro de inventario cuenta como sin existencias (`ValueError`) en lugar de romper con un error.

### 1.5 El servicio del PDF no crea la Orden
- El PDF dice: la FBV hace `Orden.objects.create(libro=libro, total=total)`, pero `procesar` del Paso 3 solo cobra y descuenta stock.
- Qué falló: al "extraer" la lógica se perdía un efecto que la vista original sí tenía.
- Qué hice: `procesar` también crea la `Orden`, para que el comportamiento sea el mismo que el de la FBV.

### 1.6 La vista del Paso 2 no sirve como vista final
- El PDF dice: el CBV del Paso 2 responde `HttpResponse("Comprado via CBV")` y todavía tiene lógica de negocio; el Paso 3 solo muestra el servicio, no cómo queda la vista.
- Qué hice: la vista final llama a `procesar`, traduce `ValueError` a 400 y un pago rechazado (`None`) a 402, y cada método queda con menos de 10 líneas, como pide la conclusión del T1. La FBV y el CBV intermedios los probé por separado (la FBV funciona tal cual siempre que exista el template `compra_rapida.html`) pero no quedan en el código final.

### 1.7 El nombre del log y el directorio donde se escribe
- El PDF dice: `archivo_log = "pagos_locales_JUAN_PEREZ.log"` (ejemplo) con ruta relativa, y pide el archivo "en la raíz de su proyecto".
- Qué falló: una ruta relativa depende de la carpeta desde donde se lance el servidor. El gateway del repo base además escribía `pagos_locales.log` con otro mensaje.
- Qué hice: el archivo se llama `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log` y se escribe siempre en la raíz del proyecto (`settings.PAGOS_LOG_DIR`, que por defecto es `BASE_DIR`). Las pruebas cambian ese setting a una carpeta temporal, así que nunca dejan un log. El mensaje es el del PDF: `Transaccion exitosa por : $monto`.

### 1.8 Paquetes sin `__init__.py`
- Lo que encontré: `domain/` tenía un archivo llamado `__init.py` (falta un guion bajo) e `infra/` no tenía ninguno.
- Qué falló: Python 3 los trata como paquetes implícitos y por eso funcionaba, pero no son paquetes de verdad (las herramientas de descubrimiento y empaquetado los pueden ignorar).
- Qué hice: renombré el archivo a `__init__.py` y creé el de `infra/`.

### 1.9 README del repo base
- Lo que encontré: el README usa `from tienda.models import ...` y el PDF usa `tienda_app.models`. La app se llama `tienda_app`.
- Qué hice: corregí el README y agregué el comando `preparar_datos` para crear el libro "Clean Code en Python" (150.0, 10 unidades) y tres libros más con stock, necesarios para las tres compras de libros distintos.

### 1.10 Archivos que no deben ir al repositorio
- Lo que encontré: el repo base tiene commiteados los `__pycache__` y un `db.sqlite3` con datos y un superusuario.
- Qué hice: los saqué del índice de git y agregué `.gitignore` (incluye `*.log` y `db.sqlite3`). La evidencia de cada tutorial se genera en la máquina de quien la entrega.
- Nota de entorno: las dependencias van en `requirements.txt` con `Django>=4.2,<5.0` (el rango que pide el enunciado del T5). Las pruebas también pasan con Django 5.2, la versión con la que se generó el proyecto.

### 1.11 El IVA con float da totales con ruido y redondeos de un centavo
- El PDF dice: `float(libro.precio) * 1.19` (en la FBV y en el repo base, `CalculadorImpuestos`).
- Qué falló: con float, 210 * 1.19 da `249.89999999999998`, que aparecía en pantalla y en el log del banco; y los totales con mitades de centavo podían quedar un centavo abajo.
- Qué hice: `CalculadorImpuestos.obtener_total_con_iva` calcula con `Decimal`, redondea a centavos con `ROUND_HALF_UP` y devuelve un `Decimal` (150 da 178.50). Sigue siendo la única regla de impuestos del proyecto.

### 1.12 El enunciado no da la URL de la Compra Rápida
- El PDF dice: "realice tres compras usando la nueva vista de Compra Rápida", sin indicar la ruta.
- Qué hice: la ruta es `/compra-rapida/<id>/`. La página de inventario (T3) enlaza cada libro, y mientras tanto los ids son 1, 2, 3 y 4 tras `preparar_datos`.

## Tutorial 2

### 2.1 El `OrdenBuilder` del PDF no puede crear una Orden
- El PDF dice: `Orden.objects.create(usuario=..., total=..., direccion_envio=...)` y `from . models import Orden` dentro de `domain/builders.py`.
- Qué falló, comprobado con el código literal:
  - El import debe ser `from ..models import Orden` (el modelo está en `tienda_app`, no en `domain`).
  - El modelo `Orden` del repo base no tenía los campos `usuario` ni `direccion_envio`.
  - `Orden.libro` es obligatorio (clave foránea sin null) y el Builder no lo pasa: `IntegrityError: NOT NULL constraint failed: tienda_app_orden.libro_id`.
  - `sum(p.precio ...) * 1.19` es `Decimal * float`, que lanza `TypeError`.
- Qué hice: agregué `usuario` (null permitido) y `direccion_envio` al modelo con la migración `0002_orden_usuario_direccion_envio` (la misma del repo del profesor). El Builder suma los precios como `Decimal`, deja el IVA y su redondeo a `CalculadorImpuestos` (ver 1.11) y guarda el primer libro de la lista en `Orden.libro`. Límite conocido: como el modelo tiene un solo `libro`, una orden con varios libros distintos guarda solo el primero como libro principal (el total y el descuento de inventario sí cuentan todos). Modelar líneas de pedido queda fuera del alcance del tutorial.

### 2.2 El Builder exige un usuario que la tienda no tiene
- El PDF dice: `if not self._usuario or not self._items: raise ValueError`.
- Qué falló: ni la vista HTML ni la API (T3) exigen login, así que `usuario` es `None` o `AnonymousUser` y toda compra fallaría con "Datos insuficientes".
- Qué hice: el usuario es opcional (`Orden.usuario` admite null); lo obligatorio es la lista de productos. Una compra sin login queda como compra de invitado.

### 2.3 Dos nombres para el mismo método del servicio
- El PDF dice: T2 define `ejecutar_proceso_compra(usuario, lista_productos, direccion)`; la vista heredada del repo base y el T3 llaman a `ejecutar_compra(libro_id, cantidad, direccion, usuario)`. Además el T2 guarda el procesador en `self.procesador` y el T1 lo llama `procesador_pago`.
- Qué falló: con solo uno de los dos métodos, o la vista HTML o la API lanzan `AttributeError`.
- Qué hice: `CompraService` tiene ambos, sobre un único flujo interno (`_procesar_orden`). `ejecutar_proceso_compra` devuelve el mensaje "Orden N procesada exitosamente." como en el PDF y `ejecutar_compra` devuelve el total, como espera la vista. El atributo se llama `procesador_pago` en todo el proyecto.

### 2.4 El servicio del PDF no valida ni descuenta inventario
- El PDF dice: el servicio construye la orden, cobra y responde; no toca `Inventario`. Si el pago falla, hace `orden.delete()` y lanza `Exception("Error en la pasarela de pagos.")`.
- Qué falló: no hay error de sintaxis, pero el T3 exige que comprar por la API descuente inventario y responda 409 sin stock. Además, `orden.delete()` solo cubre el caso en que el banco devuelve `False`; si lanza una excepción queda una orden sin cobro.
- Qué hice: el flujo valida el stock de cada libro antes de empezar (`ValueError` si no alcanza; un libro sin registro de inventario cuenta como sin stock) y luego, dentro de `transaction.atomic()`, crea la orden, descuenta el inventario y cobra. Si el banco rechaza o lanza un error, se deshace todo (orden y descuento). El descuento usa `F()` con la condición `cantidad__gte`, así dos compras a la vez no dejan el stock en negativo. El mensaje de pago rechazado es el del repo base ("La transacción fue rechazada por el banco.") y no el del PDF.
- Además: `CompraView.post` del repo base atrapaba todo (`except (ValueError, Exception)`), incluso el `Http404` de un libro inexistente (respondía 400). Ahora relanza el 404.

### 2.5 El Mock no cumple el contrato `ProcesadorPago`
- El PDF dice: `class MockPaymentProcessor:` sin clase base.
- Qué hice: hereda de `ProcesadorPago`, igual que el banco, para que ambos sean intercambiables (Liskov). No cambia el mensaje `[DEBUG] Mock Payment...`.

### 2.6 El PDF solo muestra `setup_service` de `CompraView`
- El PDF dice: muestra únicamente `setup_service`, y cambia `BancoNacionalProcesador()` por `PaymentFactory.get_processor()`.
- Qué hice: apliqué ese cambio en `CompraView` y también en `CompraRapidaView`, para que el Mock funcione en las dos vistas. Las pruebas comprueban ambas.

### 2.7 Nombre del paso del Builder en la presentación
- La presentación del tema muestra `.en_direccion()` (y `.aplicar_cupon()`), pero el PDF del tutorial usa `.para_envio(...)`. Seguí el PDF (`para_envio`); `aplicar_cupon` no se pide en ningún tutorial.

### 2.8 El Mock no escribe el log
- El T2 pide la captura del `[DEBUG] Mock Payment` y el T3 pide el log de pagos. Ambos usan la misma fábrica. Con `PAYMENT_PROVIDER=MOCK` no se escribe el log (el Mock no toca el archivo), así que la evidencia del T3 debe generarse sin esa variable. Quedó escrito en las guías de cada tutorial.

## Tutorial 3

### 3.1 `stock_actual` no existe en el modelo
- El PDF dice: `LibroSerializer` con `fields = [..., 'stock_actual']`, con una nota que dice que puede ser un campo calculado o una propiedad del modelo.
- Qué falló: `Libro` no tiene ese atributo, así que el serializer falla al construirse.
- Qué hice: agregué la propiedad `Libro.stock_actual` (lee `inventario.cantidad` y devuelve 0 si el libro no tiene inventario). No requiere migración. El serializer queda tal cual el PDF.

### 3.2 `request.user` sin login es `AnonymousUser`
- El PDF dice: `usuario=request.user # Asumiendo autenticación básica o sesión`.
- Qué falló: sin sesión iniciada, `request.user` es `AnonymousUser`, que no se puede guardar en la clave foránea `Orden.usuario`.
- Qué hice: la vista pasa `request.user` solo si está autenticado y `None` si no. `Orden.usuario` admite null (migración del T2), así que la compra por la API funciona sin login y, con sesión, queda asociada al usuario. Una prueba cubre ambos casos. No se creó ningún usuario demo.

### 3.3 La API llama a un método del servicio que tenía otra firma
- El PDF dice: `servicio.ejecutar_compra(libro_id=..., direccion=..., usuario=...)`, pero el T2 define `ejecutar_proceso_compra(usuario, lista_productos, direccion)`.
- Qué hice: ver 2.3. `ejecutar_compra(libro_id, cantidad=1, direccion="", usuario=None)` existe y es el que usa la API; `cantidad` es opcional, así que el payload del enunciado (sin cantidad) sigue valiendo.

### 3.4 Un libro inexistente daba error 500
- El PDF dice: `except ValueError` devuelve 409 y cualquier otra excepción devuelve 500.
- Qué falló: el servicio usa `get_object_or_404`, que lanza `Http404` (no es `ValueError`); la API lo devolvía como "Error interno" 500.
- Qué hice: la API captura `Http404` y responde 404 con `{"error": "El libro no existe."}`. Un pago rechazado por el banco sigue siendo 500, como en el PDF, pero ahora queda registrado con `logger.exception`.

### 3.5 Límites en el serializer de entrada
- El PDF dice: `libro_id = IntegerField()` sin límites. El repo base agregó `cantidad` (mínimo 1).
- Qué falló: sin tope, `cantidad` de cien millones arma en memoria una lista enorme antes de validar el stock, y un `libro_id` gigante puede desbordar el entero de SQLite.
- Qué hice: `libro_id` entre 1 y 2147483647 y `cantidad` entre 1 y 100; fuera de rango responde 400. Un libro sin registro de inventario responde 409 (sin stock) y no 404.

### 3.6 La ruta del endpoint
- El PDF dice: el docstring documenta `POST /api/comprar/`, el paso 4 registra `api/v1/comprar/`, y el Tutorial 5 prueba `/api/v1/comprar/`. `tienda_app/urls.py` se incluye en la raíz del proyecto, así que la ruta real es `/api/v1/comprar/`. Corregí el docstring.

### 3.7 La vista HTML de inventario no existe
- El PDF dice: "muestre que al comprar por API, la vista HTML de inventario refleja el cambio", pero el repo no tiene esa vista (y `compra.html` enlaza a `/`, que daba 404).
- Qué hice: `InventarioView` en `/inventario/` (y en `/`, que arregla el enlace "Volver a la tienda"), con el template `inventario.html` que lista id, libro, precio y stock con enlaces a las compras. Usa `InventarioService`, el mismo servicio que alimenta la API de productos.

### 3.8 `/api/v1/productos/` no está en ningún PDF
- El Tutorial 6 pide un GET a `/api/v1/productos/` ("debe responder Django") y ningún enunciado lo define. Agregué `ProductoListAPIView`, que devuelve la lista de libros con `LibroSerializer` (precio como texto, por defecto de DRF: `"150.00"`).

### 3.9 Dependencias y nombres de archivo de la entrega
- El PDF dice: `pip install djangorestframework markdown django-filter`, o bien instalar con conda. Solo hace falta `rest_framework` en `INSTALLED_APPS`; `markdown` (mejora la interfaz web) y `django-filter` no se usan todavía. Quedan en `requirements.txt` porque el PDF los instala.
- La entrega habla de "ambos archivos" pero lista tres evidencias (log, captura del POST, vista HTML). En `entrega/tutorial-03-DRF/` los archivos de código se llaman `api_views.py` y `serializers.py` (copias de `tienda_app/api/views.py` y `serializers.py`, para que no se confundan con `views.py` del resto de la app).

### 3.10 La evidencia del T3 no se puede generar con el Mock
- El PDF dice: "el sistema debe generar el log de pagos (usando la Factory que configuró la semana pasada)". Con `PAYMENT_PROVIDER=MOCK` no hay log. Las guías piden correr sin esa variable.

### 3.11 La interfaz web de DRF
- Con DRF, abrir `/api/v1/comprar/` en el navegador muestra "Method GET not allowed" (405), pero la página incluye el formulario para enviar el POST con JSON. Se verificó en un navegador real que pegar el JSON en "Content" y presionar POST devuelve 201.

## Verificado y no verificado

- Verificado: 75 pruebas automáticas (Django 4.2 y 5.2), y una prueba de humo con `runserver` y `curl`: tres compras HTML, compras por API, errores 400, 404 y 409, el log del estudiante y el `[DEBUG] Mock Payment` en la consola.
- No verificado: Postman (se probó con `curl` y con la interfaz web de DRF, que envían la misma petición), Windows y Anaconda (los comandos de esos entornos están tomados de los PDF y de la documentación, no probados), y PostgreSQL (el proyecto usa SQLite).
