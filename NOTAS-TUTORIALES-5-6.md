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
