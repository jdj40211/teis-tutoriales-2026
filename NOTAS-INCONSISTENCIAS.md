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
