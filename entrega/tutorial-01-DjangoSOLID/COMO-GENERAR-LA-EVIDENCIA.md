# Tutorial 1: Cómo generar la evidencia

La evidencia que pide el enunciado es el archivo `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log` con al menos 3 transacciones, más el documento `resumen_codigo.md` que ya está en esta carpeta. El log no viene incluido: lo genera usted al correr el proyecto, y el gateway lo crea en la raíz del proyecto la primera vez que se hace una compra.

Todos los comandos se ejecutan desde la raíz del proyecto (la carpeta donde está `manage.py`).

## 1. Entorno

Mac o Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Si usa Anaconda, no necesita el `venv`: active su entorno e instale con el mismo `pip install -r requirements.txt`.

## 2. Base de datos y libros de prueba

```bash
python manage.py preparar_datos
```

Aplica las migraciones y crea cuatro libros con stock. Los ids quedan así:
- 1: Clean Code en Python, 150.0, 10 unidades
- 2: Arquitectura Limpia, 250.0, 5 unidades
- 3: Patrones de Diseño en Python, 180.0, 8 unidades
- 4: Django para Profesionales, 210.0, 6 unidades

Esos ids suponen una base de datos nueva. Si ya tenía libros guardados, los ids pueden ser otros: abra http://127.0.0.1:8000/inventario/ con el servidor corriendo (o el shell de Django) y use los ids de la primera columna.

## 3. Asegúrese de no tener el Mock activado

El procesador Mock (Tutorial 2) no escribe el log. Verifique que la variable esté vacía:

```bash
echo $PAYMENT_PROVIDER
```

Debe imprimir una línea en blanco. Si imprime `MOCK`, ejecute `unset PAYMENT_PROVIDER` (en PowerShell: `Remove-Item Env:PAYMENT_PROVIDER`).

## 4. Levante el servidor

```bash
python manage.py runserver
```

## 5. Haga tres compras de libros diferentes

Opción A, desde el navegador (la más simple):

1. Abra http://127.0.0.1:8000/compra-rapida/1/ y presione "Comprar Ya". Debe ver "Compra exitosa".
2. Repita con http://127.0.0.1:8000/compra-rapida/2/
3. Repita con http://127.0.0.1:8000/compra-rapida/3/

Opción B, desde otra terminal con `curl`. Estas vistas protegen el POST con CSRF, así que primero se pide la página para obtener la cookie y luego se envía el POST con el token:

```bash
for id in 1 2 3; do
  curl -s -c cookies.txt http://127.0.0.1:8000/compra-rapida/$id/ > /dev/null
  TOKEN=$(grep csrftoken cookies.txt | awk '{print $7}')
  curl -s -b cookies.txt -X POST -H "X-CSRFToken: $TOKEN" http://127.0.0.1:8000/compra-rapida/$id/ | grep -i "compra exitosa"
done
rm -f cookies.txt
```

Cada vuelta debe imprimir la línea "Compra exitosa. Total: ...".

## 6. Localice el log

En la raíz del proyecto debe aparecer el archivo con su nombre:

```bash
ls pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log
cat pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log
```

Debe tener una línea por compra, con la forma `[fecha y hora] Transaccion exitosa por : $monto`. Si tiene al menos tres líneas, ya está. No edite el archivo a mano.

## 7. Entrega

En la asignación "tutorial01-DjangoSOLID" suba:
- El archivo `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log` que acaba de generar.
- El documento `resumen_codigo.md` de esta carpeta (o su versión en PDF o Word). Revíselo y ajuste el párrafo con sus propias palabras si lo desea.

## Si algo falla

- "No hay existencias": el libro se agotó. Ejecute `python manage.py preparar_datos reiniciar` para volver al stock inicial.
- 404: el id del libro no existe. Corra primero `python manage.py preparar_datos`.
- El log no aparece: confirme que está en la carpeta donde está `manage.py` y que `PAYMENT_PROVIDER` no sea `MOCK`.
