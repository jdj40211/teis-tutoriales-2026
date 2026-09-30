# Tutorial 6: El primer estrangulamiento (Django v1 y Flask v2)

Estudiante: Juan David Sierra Orozco. Materia: Tópicos Especiales en Ingeniería de Software (EAFIT).

Esta guía lleva a su EC2 la arquitectura del Tutorial 6: Nginx al frente, el monolito Django (v1), el microservicio Flask de pagos (v2) y PostgreSQL. Le dice también cómo tomar cada captura que pide el enunciado.

Este paquete no trae ninguna evidencia hecha. Las tres pruebas (Postman GET, Postman POST y logs) las produce usted en su instancia, con su IP.

Convenciones: `<IP-EC2>` es la IP pública de su instancia, `<usuario-github>` y `<repo>` son los de su repositorio, y `<carpeta-del-proyecto>` es la carpeta donde está clonado el proyecto en la EC2.

Se asume que ya hizo el Tutorial 5 (Nginx y Gunicorn) en esta EC2 con la guía de su carpeta. Si no, haga primero los pasos B.1 a B.5 de esa guía (SSH, clonar, Security Group con el puerto 80 abierto).

## Lo que contiene esta carpeta

| Archivo | Va en su proyecto como | Para qué sirve |
| :--- | :--- | :--- |
| `app.py` | `microservicio_pagos/app.py` | El microservicio Flask con `POST /api/v2/comprar` |
| `Dockerfile-flask` | `microservicio_pagos/Dockerfile` | Imagen de Flask (`python:3.11-alpine`, con Gunicorn) |
| `nginx.conf` | `nginx/nginx.conf` | Upstreams `django_v1` y `flask_v2` y el ruteo por versión |
| `docker-compose.yml` | `docker-compose.yml` (raíz) | Servicios `db`, `web_django`, `pagos_flask` y `nginx` |
| `Dockerfile` | `Dockerfile` (raíz) | Imagen de Django (`python:3.11-slim`), igual que el Tutorial 5 |
| `requirements.txt` | `requirements.txt` (raíz) | Dependencias de Django, igual que el Tutorial 5 |
| `.dockerignore` | `.dockerignore` (raíz) | Lo que no entra a la imagen de Django (ahora también `microservicio_pagos/`) |

Lo que cambia respecto al Tutorial 5, para que no le sorprenda:

- El servicio `web` ahora se llama `web_django`. Los comandos que antes usaban `web` ahora usan `web_django` (por ejemplo `docker compose exec web_django python manage.py migrate`).
- Hay un servicio nuevo, `pagos_flask`, con su propia imagen, y Nginx enruta por la versión de la API.
- El `nginx.conf` tiene un formato de log propio (`log_format estrangulador`) que agrega `backend=` y `upstream=`. Es lo que hace visible a qué backend fue cada petición en los logs; el log por defecto de Nginx no lo dice.
- El PDF del tutorial omite la ruta raíz (`location /`) que venía del Tutorial 5. Se conservó: sin ella, `/inventario/` daría 404.
- Se conservó la contraseña `secret_password` del enunciado, que es solo de laboratorio. No la reutilice en ningún sistema real.

## Parte A: en su computador

### A.1 Pruebas antes de subir (opcional)

```bash
python manage.py test
```

Deben pasar las 75 pruebas. El microservicio Flask no entra en ellas.

### A.2 Subir los cambios a SU repositorio de GitHub

Use su propio repositorio, no el del profesor (`origin`, cuenta `Nram94`).

Opción 1, con el repositorio git completo. El tag `tutorial-06` marca el estado exacto de este tutorial:

```bash
# Solo si todavía no agregó su repositorio como remoto "mio" (ver la guía del Tutorial 5)
git remote add mio https://github.com/<usuario-github>/<repo>.git

git push mio tutorial-06:main
```

Si sube con `git push` desde otra rama, asegúrese de que la carpeta `microservicio_pagos/` esté incluida.

Opción 2, copiando archivos: copie cada archivo de la tabla a la ruta indicada (renombre `Dockerfile-flask` a `microservicio_pagos/Dockerfile`), y luego:

```bash
git add microservicio_pagos nginx/nginx.conf docker-compose.yml
git commit -m "Tutorial 6: microservicio Flask y ruteo estrangulador"
git push origin main
```

(En esta opción `origin` es el remoto de SU repositorio.)

## Parte B: en la EC2

### B.1 Descargar y reconstruir

```bash
ssh -i labsuser.pem ubuntu@<IP-EC2>
cd <carpeta-del-proyecto>
git pull origin main
docker compose up -d --build --remove-orphans
```

`--remove-orphans` es necesario si venía del Tutorial 5: el servicio `web` ya no existe en el compose nuevo, pero su contenedor viejo sigue corriendo y Compose lo avisa como "orphan". Con la bandera queda eliminado y `docker ps` muestra solo los cuatro contenedores correctos.

### B.2 Reiniciar Nginx (paso que el PDF no menciona, y es obligatorio)

```bash
docker compose restart nginx
```

Nginx lee su configuración al arrancar. `docker compose up` no recrea el contenedor de Nginx si solo cambió `nginx/nginx.conf` (el compose quedó igual en ese servicio), y se queda con la configuración del Tutorial 5 en memoria. El síntoma es exactamente este: `POST /api/v2/comprar` responde 404 y lo atiende Django, no Flask. Se comprobó en pruebas locales: antes del reinicio, 404; después, 200 desde Flask.

### B.3 Verificar los cuatro contenedores

```bash
docker ps
```

Deben verse `nginx`, `web_django`, `pagos_flask` y `db`, todos `Up` (los nombres llevan el prefijo de la carpeta, por ejemplo `<carpeta>-pagos_flask-1`). `web_django` no muestra puerto publicado (solo `8000/tcp`); `pagos_flask` sí publica `0.0.0.0:5000->5000/tcp` y `nginx` el `0.0.0.0:80->80/tcp`.

### B.4 Datos de prueba

Si viene del Tutorial 5 en esta misma EC2, la base ya tiene tablas y libros (el volumen `postgres_data` se conserva). Si la base está vacía (instancia nueva o usó `down -v`), cree tablas y datos dentro del contenedor:

```bash
docker compose exec web_django python manage.py migrate
docker compose exec web_django python manage.py preparar_datos
```

### B.5 Pruebas rápidas desde la EC2

```bash
# v1: debe responder Django, con la lista de libros en JSON
curl -i http://localhost/api/v1/productos/

# v2: debe responder Flask
curl -i -X POST http://localhost/api/v2/comprar \
  -H "Content-Type: application/json" \
  -d '{"producto_id": 1, "cantidad": 2}'

# Flask directo por el puerto 5000 (solo funciona desde la EC2)
curl -i -X POST http://localhost:5000/api/v2/comprar \
  -H "Content-Type: application/json" \
  -d '{"producto_id": 1}'
```

### B.6 Security Group

El puerto 80 ya debe estar abierto desde el Tutorial 5 (EC2, Security Groups, grupo de su instancia, Edit inbound rules, HTTP, 80, `0.0.0.0/0`). No abra el 5000: el compose lo publica "solo para pruebas iniciales", como dice el enunciado, y sin regla en el Security Group solo se alcanza desde la propia EC2. Tampoco abra el 8000.

## Parte C: las tres evidencias que pide el enunciado

El enunciado pide un documento PDF con las tres. Haga las capturas en este orden, porque el log de la tercera necesita que las peticiones de las dos primeras ya existan.

### Evidencia 1: Coexistencia (v1) con Postman

1. En Postman, nueva petición: método GET, URL `http://<IP-EC2>/api/v1/productos/`.
2. Send.
3. La captura debe mostrar la URL, el estado `200 OK` y el cuerpo en Pretty JSON con los libros, por ejemplo `"titulo": "Clean Code en Python"` y `"stock_actual"`.

Esto demuestra que `/api/v1/` sigue siendo atendida por Django. Equivalente con curl: `curl -i http://<IP-EC2>/api/v1/productos/`.

### Evidencia 2: Estrangulamiento (v2) con Postman

1. Nueva petición: método POST, URL `http://<IP-EC2>/api/v2/comprar` (sin barra final).
2. Pestaña Body, opción raw, tipo JSON (el selector dice "Text" por defecto, cámbielo a JSON). Postman agrega solo `Content-Type: application/json`.
3. Pegue este cuerpo:

```json
{
  "producto_id": 1,
  "cantidad": 2
}
```

4. Send. La captura debe mostrar la URL, el método POST, el cuerpo enviado, el estado `200 OK` y esta respuesta:

```json
{
    "cantidad": 2,
    "mensaje": "Compra procesada exitosamente por el Microservicio Flask (v2)",
    "producto_id": 1,
    "status": "Aprobado"
}
```

Equivalente con curl (Linux, macOS o Git Bash):

```bash
curl -i -X POST http://<IP-EC2>/api/v2/comprar \
  -H "Content-Type: application/json" \
  -d '{"producto_id": 1, "cantidad": 2}'
```

En PowerShell de Windows las comillas del JSON se escapan distinto:

```powershell
curl.exe -i -X POST http://<IP-EC2>/api/v2/comprar -H "Content-Type: application/json" --data-raw '{\"producto_id\": 1, \"cantidad\": 2}'
```

Prueba de validación (opcional, buena para mostrar que hay lógica en el microservicio): el mismo POST con cuerpo `{"cantidad": 2}` debe responder `400` con `{"error": "Falta el ID del producto"}`.

### Evidencia 3: Logs de orquestación

En la sesión SSH de la EC2, después de hacer las dos peticiones anteriores:

```bash
docker compose logs nginx
```

Para ver solo las peticiones y descartar el ruido de arranque:

```bash
docker compose logs nginx | grep backend=
```

Debe ver líneas como estas (sus IP y horas serán otras; lo importante son `backend=` y el puerto de `upstream=`):

```text
nginx-1  | <ip> [fecha] "GET /api/v1/productos/ HTTP/1.1" 200 backend=django_v1 upstream=<ip-interna>:8000
nginx-1  | <ip> [fecha] "POST /api/v2/comprar HTTP/1.1" 200 backend=flask_v2 upstream=<ip-interna>:5000
```

Cómo se distinguen los dos backends en el log:

- `backend=django_v1` o `backend=flask_v2`: el nombre lógico, fijado por cada `location` del `nginx.conf`.
- `upstream=...:8000` es Django (Gunicorn) y `upstream=...:5000` es Flask. La IP es la privada del contenedor dentro de la red de Docker.

Esa es la prueba de que dos rutas de la misma IP y del mismo puerto 80 fueron atendidas por dos contenedores distintos. La captura debe mostrar el comando y al menos una línea de cada backend.

## Problemas frecuentes

**502 Bad Gateway.** Nginx está arriba pero no puede hablar con el backend. Ejecute `docker ps`: el contenedor `pagos_flask` (o `web_django`) debe estar `Up`. Si está caído o reiniciándose, lea el motivo con `docker compose logs pagos_flask` (busque errores de indentación o de sintaxis en `app.py`). El log de Nginx lo confirma con `connect() failed ... while connecting to upstream`. Si el backend está bien pero sigue el 502 después de reconstruirlo, reinicie Nginx: `docker compose restart nginx`.

**404 en `/api/v2/comprar` pero `/api/v1/` funciona.** Hay tres causas, en este orden de probabilidad:
1. Nginx sigue con la configuración vieja en memoria (la del Tutorial 5). Solución: `docker compose restart nginx`. Se nota en el log: las líneas nuevas no traen el campo `backend=` (todavía es el formato por defecto) y la petición a `/api/v2/comprar` termina en 404.
2. Puso una barra final: `/api/v2/comprar/`. Nginx la manda a Flask, pero la ruta de Flask es exactamente `/api/v2/comprar` y responde 404. Quite la barra.
3. La ruta en `nginx.conf` (`location /api/v2/comprar`) y en Flask (`@app.route('/api/v2/comprar')`) no coinciden. Nginx pasa la ruta completa, sin recortarla; en Flask la ruta no puede ser solo `/comprar`.

**405 Method Not Allowed en v2.** Hizo un GET (por ejemplo, abriendo la URL en el navegador). La ruta v2 solo acepta POST: use Postman o curl con `-X POST`.

**415 Unsupported Media Type en v2.** El POST no llevó `Content-Type: application/json`. En Postman: Body, raw, tipo JSON. En curl: `-H "Content-Type: application/json"`.

**El contenedor `nginx` se cae al arrancar con `host not found in upstream "pagos_flask:5000"`.** Nginx resuelve los nombres al iniciar. Si el contenedor `pagos_flask` no existe (por ejemplo, su imagen falló al construirse), Nginx no arranca. Revise `docker compose ps -a` y `docker compose logs pagos_flask`, arregle el error, y ejecute `docker compose up -d --build`. Los nombres de servicio del compose deben coincidir letra por letra con los del `nginx.conf` (`web_django`, `pagos_flask`). No defina `networks:` a mano: todos los servicios comparten la red que Compose crea y así se ven por nombre.

**Cambié `nginx.conf` y no se ve el cambio.** `docker compose restart nginx`. Use `restart` y no `nginx -s reload`: git reemplaza el archivo por uno nuevo y el contenedor puede seguir viendo el viejo hasta reiniciarse.

**Aparece el aviso "Found orphan containers".** Es el contenedor `web` del Tutorial 5. Ejecute `docker compose up -d --remove-orphans`.

**Django dice que no existe la tabla `tienda_app_libro`, o `/api/v1/productos/` devuelve 500.** La base está vacía: parte B.4, con `web_django`. Si no repitió las variables `DB_*` en el servicio `web_django` del compose, Django usa SQLite y no ve la base de PostgreSQL; el compose de esta carpeta ya las trae.

**`web_django` no arranca por la base de datos.** Compruebe que `db` esté `Up (healthy)`. El compose espera ese estado; con un compose antiguo sin `healthcheck`, corra `docker compose up -d` de nuevo.

## Al terminar: no gaste créditos

- Bajar los contenedores (conserva los datos): `docker compose down`.
- Bajar todo y borrar la base, el volumen y las imágenes construidas: `docker compose down -v --rmi local`.
- Detenga la instancia desde la consola (EC2, Instances, Instance state, Stop instance) o use End Lab en el Learner Lab. Una EC2 encendida gasta créditos aunque no la use.
- Si tiene una base RDS del tutorial anterior y ya no la necesita, bórrela desde la consola de RDS. Consume créditos mientras exista.
- Las capturas son suyas: revise que ninguna muestre llaves, tokens ni contraseñas reales antes de entregarlas.
