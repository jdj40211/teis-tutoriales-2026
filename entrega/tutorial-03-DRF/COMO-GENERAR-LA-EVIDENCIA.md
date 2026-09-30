# Tutorial 3: Cómo generar la evidencia

Lo que pide el enunciado:
1. El log de pagos generado por la Factory configurada en el Tutorial 2, con el inventario descontado.
2. Una demostración de que al comprar por la API, la vista HTML de inventario refleja el cambio (las dos "puertas", HTML y API, llegan a la misma lógica de negocio).
3. Una captura de pantalla de un POST a `/api/v1/comprar/` hecho con Postman o con la interfaz web de DRF.

Nada de esto viene incluido en el proyecto. Usted lo genera y toma las capturas. `EVIDENCIA-TUTORIAL-3.md` es la lista de control para no olvidar nada.

Todos los comandos se ejecutan desde la raíz del proyecto (donde está `manage.py`), con el entorno virtual activado (ver el Tutorial 1, paso 1; el `requirements.txt` ya incluye Django REST framework).

## 1. Partir limpio

```bash
python manage.py preparar_datos reiniciar
```

Deja el stock inicial (libro 1: 10 unidades, libro 2: 5, libro 3: 8, libro 4: 6) y borra las órdenes anteriores.

Los ids 1 a 4 de este documento suponen una base de datos que empezó vacía. Si ya tenía libros guardados, los ids pueden ser otros: mírelos en la primera columna de http://127.0.0.1:8000/inventario/ y cámbielos en los payloads.

## 2. Importante: sin el Mock

El log de pagos lo escribe el banco real. El Mock (Tutorial 2) no escribe el archivo. Verifique que la variable esté vacía:

```bash
echo $PAYMENT_PROVIDER
```

Debe salir una línea en blanco. Si sale `MOCK`: `unset PAYMENT_PROVIDER` (PowerShell: `Remove-Item Env:PAYMENT_PROVIDER`).

## 3. Levante el servidor

```bash
python manage.py runserver
```

## 4. Captura "antes": la vista HTML del inventario

Abra http://127.0.0.1:8000/inventario/ en el navegador y tome una captura con la columna "Stock" visible. Los ids de los libros están en la primera columna. Opcional: http://127.0.0.1:8000/api/v1/productos/ muestra los mismos datos en JSON.

## 5. Compre por la API

### Opción A: Postman

1. Nueva petición, método POST, URL `http://127.0.0.1:8000/api/v1/comprar/`
2. Pestaña Body, opción raw, tipo JSON. Postman agrega solo el encabezado `Content-Type: application/json`.
3. Pegue uno de estos payloads y presione Send.

Compra del libro 1:

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 123 #45-67, Medellin"
}
```

Compra del libro 2:

```json
{
  "libro_id": 2,
  "direccion_envio": "Carrera 43A #1-50, Medellin"
}
```

Compra del libro 3:

```json
{
  "libro_id": 3,
  "direccion_envio": "Avenida 80 #70-20, Medellin"
}
```

Compra de 2 unidades del libro 4 (el campo `cantidad` es opcional y por defecto vale 1):

```json
{
  "libro_id": 4,
  "direccion_envio": "Calle 10 #30-15, Medellin",
  "cantidad": 2
}
```

La respuesta correcta tiene estado HTTP 201 Created y un JSON con `"estado": "exito"` y un mensaje que incluye el total con IVA. Tome la captura de Postman mostrando la petición y la respuesta.

### Opción B: interfaz web de DRF

1. Abra http://127.0.0.1:8000/api/v1/comprar/ en el navegador. Verá "Method GET not allowed" porque ese endpoint solo acepta POST, pero abajo aparece el formulario.
2. En "Media type" deje `application/json`.
3. En "Content" pegue el JSON (por ejemplo el del libro 1) y presione el botón POST.
4. La página se recarga con la respuesta (201 Created). Capture la pantalla completa.

### Opción C: curl

```bash
curl -i -X POST -H "Content-Type: application/json" -d '{"libro_id": 1, "direccion_envio": "Calle 123 #45-67, Medellin"}' http://127.0.0.1:8000/api/v1/comprar/
```

En Windows CMD las comillas simples no funcionan; use comillas dobles con barras invertidas: `-d "{\"libro_id\": 1, \"direccion_envio\": \"Calle 123 #45-67, Medellin\"}"`.

## 6. Captura "después": la vista HTML refleja el cambio

Recargue http://127.0.0.1:8000/inventario/ y tome otra captura. El stock del libro comprado debe haber bajado en la cantidad comprada. Esa pareja de capturas (antes y después) es la prueba de que la API y la vista HTML comparten la misma lógica de negocio.

## 7. El log de pagos

```bash
cat pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log
```

(En Windows: `type pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log`.) Debe tener una línea por cada compra hecha con la API. Si antes ya hizo las compras del Tutorial 1 con este mismo proyecto, el archivo también tendrá esas líneas; eso está bien.

## 8. Errores que conviene probar (opcional, sirven para entender el diseño)

Falta un campo, responde 400 Bad Request:

```json
{
  "libro_id": 1
}
```

Libro que no existe, responde 404 Not Found:

```json
{
  "libro_id": 999,
  "direccion_envio": "Calle 1"
}
```

Más unidades que el stock, responde 409 Conflict y el inventario no cambia:

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 1",
  "cantidad": 100
}
```

## 9. Entrega

En la asignación "tutorial0-3 DRF&API" suba:
- El archivo de log `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log`.
- La captura del POST a `/api/v1/comprar/` (Postman o interfaz web de DRF).
- Las capturas del inventario antes y después.
- Si la plataforma pide código, `api_views.py` y `serializers.py` de esta carpeta.

El enunciado dice "suba ambos archivos" aunque lista varias evidencias; ante la duda, suba todo lo anterior.

## Si algo falla

- `Connection refused`: el servidor no está corriendo o usa otro puerto.
- 400 con `{"libro_id": ["A valid integer is required."]}`: el id debe ser un número, sin comillas.
- Postman responde 415 o 400 por formato: confirme Body raw con tipo JSON.
- El log no aparece: probablemente está activo `PAYMENT_PROVIDER=MOCK`.
- El stock no cambia entre capturas: recargue la página (Cmd/Ctrl + R) y revise que la respuesta haya sido 201.
