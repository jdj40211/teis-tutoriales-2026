# Tutorial 2: Cómo generar la evidencia

Lo que pide el enunciado:
1. Una captura de pantalla de la consola de Django mostrando el mensaje "[DEBUG] Mock Payment..." al hacer una compra con la variable de entorno activada.
2. Los archivos `infra/factories.py` y `domain/builders.py` (están en esta carpeta).
3. La reflexión, un párrafo breve que usted escribe con sus palabras. En `PUNTOS-PARA-LA-REFLEXION.md` hay ideas de apoyo.

La captura la toma usted: aquí no hay ninguna incluida. Todos los comandos se ejecutan desde la raíz del proyecto (donde está `manage.py`), con el entorno virtual activado (ver el paso 1 del Tutorial 1).

## 1. Datos de prueba

```bash
python manage.py preparar_datos
```

Si ya hizo compras antes y quiere empezar con el stock inicial: `python manage.py preparar_datos reiniciar`.

Los ejemplos de este documento usan el libro con id 1 (Clean Code en Python), que es el primero si la base de datos estaba vacía. Si ya tenía libros guardados, abra http://127.0.0.1:8000/inventario/ y use los ids de la primera columna.

## 2. Levante el servidor con el Mock activado

Mac, Linux o Git Bash:

```bash
PAYMENT_PROVIDER=MOCK python manage.py runserver
```

Windows PowerShell:

```powershell
$env:PAYMENT_PROVIDER="MOCK"; python manage.py runserver
```

Windows CMD:

```bat
set PAYMENT_PROVIDER=MOCK
python manage.py runserver
```

La variable solo vale para esa terminal y para ese servidor. No cierre esa ventana: es la "consola de Django" que debe aparecer en la captura.

## 3. Haga una compra

Desde el navegador, con el servidor corriendo:

- Flujo de la Compra Rápida: http://127.0.0.1:8000/compra-rapida/1/ y el botón "Comprar Ya".
- Flujo de la vista principal: http://127.0.0.1:8000/compra/1/ y el botón "Confirmar Pago con Banco Nacional" (el texto del botón no cambia aunque el Mock esté activo).

Alternativa con `curl` desde una segunda terminal (el POST necesita el token CSRF):

```bash
curl -s -c cookies.txt http://127.0.0.1:8000/compra/1/ > /dev/null
TOKEN=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -s -b cookies.txt -X POST -H "X-CSRFToken: $TOKEN" http://127.0.0.1:8000/compra/1/ | grep -i "gracias"
rm -f cookies.txt
```

## 4. Revise la consola del servidor

En la terminal donde corre `runserver` debe aparecer una línea que empieza por `[DEBUG] Mock Payment: Procesando pago de $` y termina en `sin cargo real.`, justo antes de la línea de registro de la petición POST.

Tome la captura de esa ventana con la línea visible:
- Mac: Cmd + Shift + 4 y seleccione la ventana.
- Windows: Win + Shift + S.

## 5. Comprobación opcional: el Mock no toca el banco

Con el Mock activo no se crea ni se modifica el archivo `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log`. Si detiene el servidor y lo levanta sin la variable (`python manage.py runserver`), la misma compra sí escribe una línea nueva en ese archivo. Eso demuestra que la fábrica cambió el comportamiento sin cambiar el código.

## 6. Entrega

Suba la captura de pantalla, `factories.py`, `builders.py` y su reflexión.

## Si algo falla

- No aparece el `[DEBUG]`: la variable no llegó al servidor. Verifique que la escribió en la misma terminal y en el mismo comando (`echo $PAYMENT_PROVIDER` debe imprimir `MOCK`).
- Error 400 con "No hay suficiente stock": ejecute `python manage.py preparar_datos reiniciar`.
- Si abre la terminal de nuevo, vuelva a definir la variable.
