# Notas de los tutoriales 5 y 6

Autor: Juan David Sierra Orozco. Materia: Tópicos Especiales en Ingeniería de Software (EAFIT).

Este archivo sigue el mismo formato de `NOTAS-INCONSISTENCIAS.md`: qué decía el PDF, qué falló o qué faltaba, qué hice. Las pruebas se hicieron con Docker en local (OrbStack) y las capturas de evidencia las produce el estudiante en su EC2.

## Tutorial 4 base (etapa previa, tag `tutorial-04-base`)

El Tutorial 5 dice "Tutorial 04 completado (aplicación dockerizada)", pero el proyecto usaba SQLite y no tenía nada de Docker. Se dejó lo mínimo para que esa base exista.

### 4.1 Nombre de la carpeta del proyecto
- El PDF dice: `gunicorn tienda_project.wsgi:application`, con el comentario "debe ser el nombre de la carpeta donde está su wsgi.py".
- Lo que encontré: la carpeta de este proyecto se llama `Tienda` (`Tienda/wsgi.py`).
- Qué hice: el comando es `gunicorn Tienda.wsgi:application --bind 0.0.0.0:8000`.

### 4.2 Base de datos por variables de entorno
- El PDF dice: el compose define `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`, pero `settings.py` no las leía (usaba SQLite fija).
- Qué hice: si existe `DB_HOST`, `settings.py` usa PostgreSQL con esas variables. Sin `DB_HOST` sigue SQLite, así que las 75 pruebas y `runserver` local no cambian.

### 4.3 Imagen base: `python:3.11-slim`, no alpine
- `psycopg2-binary` no publica ruedas para musl (alpine). Con alpine habría que instalar `gcc` y `libpq-dev` para compilarlo. Para Flask (sin psycopg2) sí se usa alpine, como pide el T6.

### 4.4 `requirements.txt`
- Quedó `Django>=4.2,<5.0`, `djangorestframework`, `markdown`, `django-filter` (los de T3), `psycopg2-binary` y `gunicorn` (los del T5), más `whitenoise` (ver 5.4). Las 75 pruebas pasan con Django 4.2.30.

### 4.5 `ALLOWED_HOSTS`
- El proyecto tenía `ALLOWED_HOSTS = []`. Con `DEBUG=True` eso solo acepta `localhost`; detrás de Nginx la cabecera `Host` trae la IP de la EC2 y Django respondería 400 (DisallowedHost).
- Qué hice: `DJANGO_ALLOWED_HOSTS` (separado por comas) con valor por defecto `localhost,127.0.0.1,[::1]`. El compose pone `*` para el laboratorio. En un sistema real se pone la IP o el dominio.

### 4.6 `DEBUG` configurable
- `DJANGO_DEBUG` (por defecto encendido, igual que antes). Existe para poder probar el comportamiento con `DEBUG=False` (ver 5.4).

### 4.7 `.dockerignore`
- Deja fuera `.git`, entornos virtuales, `__pycache__`, `db.sqlite3`, `*.log`, `entrega/` y el override local.

## Tutorial 5: Nginx y Gunicorn

### 5.1 Las migraciones y los datos no se corren solos
- El PDF dice: `docker compose up -d --build` y verificar con `docker ps`. No dice cómo se crean las tablas en PostgreSQL.
- Qué falló: la base de PostgreSQL nace vacía, y `/inventario/` fallaría con "relation tienda_app_libro does not exist".
- Qué hice: documentado en la guía: `docker compose exec web python manage.py migrate` y `docker compose exec web python manage.py preparar_datos`, dentro del contenedor (no en la EC2).

### 5.2 `depends_on` no espera a que Postgres esté listo
- El PDF dice: `depends_on: - db`.
- Qué falló (comprobado): `depends_on` solo espera a que el contenedor de la base arranque. Con `runserver` (que revisa la base al iniciar) el contenedor `web` se cayó con `connection refused`. Gunicorn conecta de forma perezosa y no se cae, pero las primeras peticiones fallarían.
- Qué hice: `healthcheck` en `db` (`pg_isready`) y `depends_on` con `condition: service_healthy` en `web`. Cambio mínimo, no altera los nombres ni los puertos.

### 5.3 La línea `version: '3.8'`
- Docker Compose v2 la ignora y emite una advertencia de que está obsoleta. La quité.

### 5.4 Archivos estáticos con Gunicorn
- El PDF no lo trata. Gunicorn no sirve estáticos (solo `runserver` lo hace), con `DEBUG` encendido o apagado. Sin nada más, la interfaz web de DRF se ve sin CSS y, peor, le faltan los `.js` del formulario con el que el estudiante puede enviar el POST desde el navegador (captura 1).
- Qué hice: `whitenoise` (un middleware y una línea en `requirements.txt`), `STATIC_ROOT` configurable y `collectstatic` en el `Dockerfile`, con `STATIC_ROOT=/opt/staticfiles`, fuera de `/app` para que el volumen `.:/app` del compose no lo tape. Comprobado con `DJANGO_DEBUG=0`: CSS y JS de DRF responden 200 a través de Nginx.
- Alternativa descartada: servir `/static/` desde Nginx con un volumen compartido. Habría cambiado el `nginx.conf` del enunciado.

### 5.5 Pantalla de la URL que pide el enunciado
- El PDF dice: captura del navegador en `http://<IP-EC2>/api/v1/comprar/`.
- Qué falló: esa vista solo admite POST, y el navegador hace GET. Responde 405.
- Qué hice: la guía explica que el 405 con la pantalla de DRF ("HTTP 405 Method Not Allowed", `Allow: POST, OPTIONS`, `"detail": "Method \"GET\" not allowed."`) prueba que Nginx enruta, y propone una segunda captura: pegar el JSON en la caja "Content" de esa misma página y presionar POST, que muestra `HTTP 201 Created`.

### 5.6 El puerto 8000 en `docker ps`
- Con el `EXPOSE 8000` del `Dockerfile`, `docker ps` muestra `8000/tcp` para `web` (sin `0.0.0.0:`). Eso significa expuesto dentro de la red de Docker, no publicado en el host. La guía lo explica para que no se confunda con un puerto abierto.

### 5.7 Aislamiento: timeout o "connection refused"
- El PDF dice que el acceso al 8000 debe dar timeout. El timeout viene del Security Group; si ese puerto estuviera abierto allí, el resultado sería "connection refused" (nada escucha en el host). Ambos demuestran el aislamiento; la guía dice cómo obtener el timeout.

### 5.8 `nginx.conf`
- El PDF (por el extractor de texto) trae espacios dentro de las directivas (`location = / favicon . ico`, `$ p r o x y _ ...`). Se transcribieron limpias. Quedó igual al enunciado salvo los comentarios en español.

### 5.9 Contraseña de ejemplo
- El compose lleva `secret_password` (la del PDF) con una advertencia en un comentario. Es para el laboratorio, no debe reutilizarse.

### 5.10 El CSRF y el puerto
- Con `proxy_set_header Host $host` (como en el PDF) Nginx quita el puerto de la cabecera `Host`. En el puerto 80 no importa. Si alguien publica Nginx en otro puerto (por ejemplo 8080 para pruebas locales), los formularios HTML de compra (`/compra/<id>/`) fallarían por CSRF, porque el `Origin` del navegador incluye el puerto y el `Host` no. La API no se ve afectada (sin sesión, DRF no exige CSRF). Se dejó `$host` como en el enunciado.

## Tutorial 6: el primer estrangulamiento (Flask v2)

### 6.1 El compose del T6 renombra `web` y no repite la base de datos
- El PDF dice: `web_django` con `build`, `command` y `depends_on`, y en `db` pone `# ... (configuración previa)`.
- Qué falló: al renombrar `web` a `web_django` había que repetir el bloque `environment` (`DB_*`). Sin él, `settings.py` no ve `DB_HOST` y cae en SQLite: `/api/v1/productos/` respondería datos de otra base (vacía, sin tablas). Tampoco están `db` ni el volumen escritos completos, ni `ALLOWED_HOSTS`.
- Qué hice: el compose quedó completo (servicios `db`, `web_django`, `pagos_flask` y `nginx`, con los nombres exactos del enunciado), con las variables de la base, el `healthcheck` y `DJANGO_ALLOWED_HOSTS=*`.

### 6.2 El `nginx.conf` del T6 pierde la ruta raíz
- El PDF dice: solo `location /api/v1/` y `location /api/v2/comprar`.
- Qué falló: sin `location /`, cualquier otra ruta (`/inventario/`, `/`, `/admin/`) da 404 de Nginx y deja de funcionar lo que el T5 dejó andando.
- Qué hice: conservé `location /` hacia `django_v1` con los mismos encabezados del T5. Nginx elige el `location` más específico, así que `/api/v1/` y `/api/v2/comprar` siguen ganando. Comprobado: `/` e `/inventario/` responden 200 y `/api/v2/comprar` va a Flask.
- Además agregué `X-Forwarded-For` y `proxy_redirect off` en las rutas v1 (como en el T5) y `X-Forwarded-For` en v2, para que los dos backends reciban la IP real del cliente. El resto es igual al PDF.
- Solo la ruta que empieza por `/api/v2/comprar` va a Flask; otra ruta `/api/v2/...` cae en `location /` y Django responde 404.

### 6.3 El log de Nginx no dice a qué backend fue la petición
- El PDF pide que `docker compose logs nginx` muestre "el redireccionamiento de las peticiones a los dos backends distintos". El log por defecto no trae el backend.
- Qué hice: un `log_format estrangulador` con `backend=$backend upstream=$upstream_addr`. Cada `location` fija `set $backend django_v1` o `flask_v2`; `upstream` muestra la IP y el puerto reales (8000 Django, 5000 Flask). El log se escribe en `/var/log/nginx/access.log`, que en la imagen oficial es un enlace a la salida estándar, así que `docker compose logs nginx` lo muestra. Comprobado con las líneas de ambos backends.

### 6.4 Nginx no recarga solo: el 404 en v2 es real
- El PDF (y `Nginx_TroubleShooting`, caso 4) mencionan reiniciar, pero el flujo del T6 dice solo `git pull` y `docker compose up -d --build`.
- Qué falló (comprobado): tras cambiar `nginx.conf` y correr `up -d --build`, Compose dejó el contenedor de Nginx sin recrear (`Running`) y con la configuración del T5 en memoria. `POST /api/v2/comprar` respondió 404 (lo atendió Django). Con `docker compose restart nginx` pasó a 200 desde Flask.
- Qué hice: la guía incluye `docker compose restart nginx` como paso obligatorio después del `up`, y explica el síntoma en los problemas frecuentes.

### 6.5 Contenedor huérfano al pasar de T5 a T6
- Al renombrar `web` a `web_django`, `docker compose up` avisa `Found orphan containers ([...-web-1])` y deja el contenedor viejo corriendo (comprobado). La guía usa `docker compose up -d --build --remove-orphans`, que lo elimina.
- Los comandos que en el T5 usaban `web` (`exec web ...`) pasan a `web_django`.

### 6.6 El puerto 5000 de Flask
- El PDF dice `ports: "5000:5000"` "solo para pruebas iniciales, luego lo cerraremos". Se dejó en el compose entregable tal cual. La guía pide no abrir el 5000 en el Security Group (queda alcanzable solo desde la propia EC2) y propone la prueba `curl` a `localhost:5000`. En el Mac de pruebas el 5000 lo ocupa macOS (AirPlay), por eso las pruebas locales lo remapearon en un override ignorado por git.

### 6.7 Imagen de Nginx
- El PDF del T6 usa `nginx:1.25` y el del T5 `nginx:1.25-alpine`. Dejé `nginx:1.25-alpine` en los dos para reutilizar la imagen ya descargada en la EC2.

### 6.8 Redes y nombres (caso 3 del anexo de Nginx)
- No hace falta declarar `networks:`: Compose pone todos los servicios en una red por defecto donde se ven por nombre. Lo que sí importa es que los nombres del `nginx.conf` (`web_django`, `pagos_flask`) coincidan con los del compose. Comprobado: si el contenedor `pagos_flask` no existe, Nginx no arranca (`[emerg] host not found in upstream "pagos_flask:5000"`); si existe pero está detenido, responde 502 (`connect() failed ... while connecting to upstream`).

### 6.9 La ruta de Flask y la barra final (caso 2 del anexo)
- La ruta es `/api/v2/comprar`, igual en Nginx y en Flask. Comprobado: `/api/v2/comprar/` (con barra) responde 404 desde Flask.
- `app.py` es el del enunciado sin cambios de lógica. Consecuencia conocida: un POST sin `Content-Type: application/json` responde 415 (Flask 3) y un GET responde 405. La guía lo explica. Se corrigieron solo los espacios que metió el extractor de texto del PDF.

### 6.10 Flask no toca la base de datos
- El endpoint es una simulación (así lo dice el PDF): responde "Aprobado" sin descontar stock. La presentación habla de base compartida para una etapa posterior. Comprobado: tras un POST a v2 el stock de Django no cambia; uno a v1 sí lo baja.

## Verificado y no verificado (Tutoriales 5 y 6)

- Verificado en Docker local (OrbStack, Compose v5.1.2, Django 4.2.30, Flask 3.1.3): los tres contenedores del T5 `Up`; `/inventario/` 200 por Nginx; `POST /api/v1/comprar/` 201 y el stock baja; el 8000 del contenedor `web` no está publicado en el host y una conexión a `localhost:8000` falla; GET a la URL de compra responde 405 con la pantalla de DRF; CSS y JS de DRF cargan por Nginx (también con `DJANGO_DEBUG=0`); T6: `/api/v1/productos/` 200 (Django), `POST /api/v2/comprar` 200 con el mensaje de Flask, sin `producto_id` 400, el log muestra ambos backends; `/inventario/` sigue en 200; las dos imágenes se construyen y arrancan para `linux/amd64`; las 75 pruebas pasan.
- No verificado: AWS real (EC2, Security Group, IP pública, el timeout del puerto 8000 desde internet), Postman (se probó con `curl`, que envía la misma petición), el envío del POST desde el formulario del navegador (se comprobó que sus archivos estáticos cargan y se probó la petición equivalente con `curl`), los comandos de PowerShell de Windows, y la ejecución completa de los dos stacks sobre un procesador x86 real (las imágenes amd64 se construyeron y arrancaron con emulación).
