# Tutorial 3: Lista de control de la evidencia

Estudiante: Juan David Sierra Orozco
Asignación: tutorial0-3 DRF&API

Este archivo no contiene evidencia. Es la lista de control y la plantilla para que usted registre la suya después de ejecutar los pasos de `COMO-GENERAR-LA-EVIDENCIA.md`. Complete cada casilla con lo que observe en su propia ejecución.

## Qué prueba cada pieza

- El log de pagos prueba que la API usa la Factory del Tutorial 2 y que el banco real (no el Mock) registró cada transacción.
- La captura del POST prueba que el endpoint `/api/v1/comprar/` valida el JSON con el serializer y responde con el código HTTP correcto.
- Las capturas del inventario, antes y después, prueban que la API y la vista HTML conducen a la misma lógica de negocio: el `CompraService`.

## Lista de control

- [ ] Ejecuté `python manage.py preparar_datos reiniciar` antes de empezar.
- [ ] `PAYMENT_PROVIDER` estaba vacío (sin Mock) durante las compras.
- [ ] Captura del inventario HTML antes de comprar por la API.
- [ ] Al menos un POST a `/api/v1/comprar/` con respuesta 201, hecho con Postman o con la interfaz web de DRF.
- [ ] Captura del POST (petición y respuesta visibles).
- [ ] Captura del inventario HTML después, con el stock distinto.
- [ ] Archivo `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log` con una línea por cada compra hecha por la API.
- [ ] Revisé que ningún archivo entregado tenga datos que no sean míos.

## Mi registro de la ejecución

Complete con lo que usted vea:

- Fecha y hora de la ejecución:
- Herramienta usada para el POST (Postman, interfaz web de DRF, curl):
- Libro comprado (id y título):
- Stock en la vista HTML antes de la compra:
- Stock en la vista HTML después de la compra:
- Código HTTP de la respuesta:
- Cantidad de líneas del log al terminar:

## Archivos de código de esta entrega

- `api_views.py`: copia de `tienda_app/api/views.py` (`CompraAPIView` y `ProductoListAPIView`).
- `serializers.py`: copia de `tienda_app/api/serializers.py` (`LibroSerializer` y `OrdenInputSerializer`).

## Nombres de archivo sugeridos para las capturas

- `01-inventario-antes.png`
- `02-post-api-comprar.png`
- `03-inventario-despues.png`
