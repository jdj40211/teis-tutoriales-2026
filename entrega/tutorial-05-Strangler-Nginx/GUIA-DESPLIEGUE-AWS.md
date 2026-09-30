# Tutorial 5: Nginx, Gunicorn y Django en AWS EC2

Estudiante: Juan David Sierra Orozco. Materia: Tópicos Especiales en Ingeniería de Software (EAFIT).

Esta guía lleva la arquitectura del Tutorial 5 (Nginx como proxy inverso, Gunicorn como servidor WSGI, Django y PostgreSQL, tres contenedores) a su EC2 de AWS Academy, y le dice cómo tomar cada captura que pide el enunciado.

Este paquete no trae ninguna evidencia hecha. Las tres capturas las produce usted en su propia instancia, con su propia IP.

Convenciones: `<IP-EC2>` es la IP pública de su instancia, `<usuario-github>` y `<repo>` son los de su repositorio, y `<carpeta-del-proyecto>` es la carpeta donde quedó clonado el proyecto dentro de la EC2 (en el enunciado aparece como `mi-proyecto-django`).

## Lo que contiene esta carpeta

| Archivo | Va en su proyecto como | Para qué sirve |
| :--- | :--- | :--- |
| `nginx.conf` | `nginx/nginx.conf` | Enrutamiento: upstream `django_backend` y proxy inverso |
| `docker-compose.yml` | `docker-compose.yml` (raíz) | Servicios `db`, `web` y `nginx` |
| `Dockerfile` | `Dockerfile` (raíz) | Imagen de Django (`python:3.11-slim`) |
| `requirements.txt` | `requirements.txt` (raíz) | Dependencias, con `gunicorn` |
| `settings.py` | `Tienda/settings.py` | Base de datos y hosts permitidos leídos del entorno |
| `.dockerignore` | `.dockerignore` (raíz) | Lo que no entra a la imagen |

Dos cosas que debe saber antes de empezar:

- La carpeta del proyecto Django se llama `Tienda`, no `tienda_project` como dice el PDF. Por eso el comando de Gunicorn es `gunicorn Tienda.wsgi:application`. Si su proyecto se llamara distinto, cambie solo esa palabra en el `command` del servicio `web`.
- La contraseña `secret_password` es la del enunciado y es solo de laboratorio. No la reutilice en ningún sistema real.

## Parte A: en su computador

### A.1 Pruebas rápidas antes de subir (opcional, 1 minuto)

Desde la raíz del proyecto, con su entorno virtual activado:

```bash
python manage.py test
```

Deben pasar las 75 pruebas.

### A.2 Subir los cambios a SU repositorio de GitHub

Use su propio repositorio. No intente subir al repositorio del profesor (`origin`, en la cuenta `Nram94`): no tiene permiso y no es lo que se pide.

Opción 1, si trabaja con el repositorio git completo (rama `tutoriales-5-6`). El tag `tutorial-05` marca exactamente el estado de este tutorial:

```bash
# Una sola vez: agregue su repositorio como un remoto nuevo llamado "mio"
git remote add mio https://github.com/<usuario-github>/<repo>.git

# Suba el estado del Tutorial 5 a la rama main de su repositorio
git push -u mio tutorial-05:main
```

Si GitHub le pide credenciales, use su usuario y un Personal Access Token (Settings, Developer settings, Personal access tokens), no su contraseña de la cuenta.

Opción 2, si solo tiene la carpeta de archivos, copie cada archivo de la tabla de arriba a la ruta indicada dentro de su repositorio, y luego:

```bash
git add Dockerfile docker-compose.yml requirements.txt .dockerignore nginx/nginx.conf Tienda/settings.py
git commit -m "Tutorial 5: Nginx como proxy inverso y Gunicorn"
git push origin main
```

(En esta opción `origin` es el remoto de SU repositorio.)

## Parte B: en la EC2

### B.1 Entrar por SSH

En AWS Academy: Learner Lab, botón Start Lab (espere el círculo verde), AWS Details, y descargue la llave (`labsuser.pem` o `.ppk`). En su terminal:

```bash
chmod 400 labsuser.pem
ssh -i labsuser.pem ubuntu@<IP-EC2>
```

La IP pública de la instancia cambia cada vez que el laboratorio se detiene y se vuelve a iniciar. Consúltela siempre en EC2, Instances, columna "IPv4 pública".

### B.2 Descargar el código

Si todavía no tiene el proyecto en la EC2:

```bash
git clone https://github.com/<usuario-github>/<repo>.git
cd <repo>
```

Si ya lo tiene clonado:

```bash
cd <carpeta-del-proyecto>
git pull origin main
```

Si tenía corriendo en esta EC2 el stack del Tutorial 4 (Django publicado en el puerto 8000), bájelo antes de levantar el nuevo para liberar el nombre y los puertos:

```bash
docker compose down
```

(Sin `-v`, la base de datos se conserva.) Si en esta instancia corre otro proyecto en el puerto 80, libérelo también: Nginx necesita ese puerto. Para ver quién lo usa:

```bash
sudo ss -tlnp | grep ':80 '
```

### B.3 Reconstruir y levantar la arquitectura

```bash
docker compose up -d --build
```

La primera vez tarda unos minutos (descarga imágenes y construye la de Django). Mientras tanto, `db` se marca "healthy" cuando PostgreSQL ya acepta conexiones, y solo entonces arranca `web`. Verifique:

```bash
docker ps
```

Deben aparecer tres contenedores `Up`: `nginx`, `web` y `db` (sus nombres llevan el prefijo de la carpeta, por ejemplo `<carpeta>-nginx-1`). Si alguno no aparece, vea la sección de problemas frecuentes.

### B.4 Crear las tablas y los datos de prueba (dentro del contenedor)

El PDF no lo dice, pero la base PostgreSQL nace vacía y Django no crea las tablas solo. Hay que correr los comandos dentro del contenedor `web`, no en la EC2:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py preparar_datos
```

`preparar_datos` crea cuatro libros con stock (ids 1 a 4; el 1 es "Clean Code en Python", 10 unidades). Se puede repetir sin duplicar datos. Para volver al stock inicial: `docker compose exec web python manage.py preparar_datos reiniciar`.

### B.5 Abrir el puerto 80 en el Security Group (firewall de AWS)

1. Entre a la consola de AWS desde el Learner Lab (botón AWS con el círculo verde).
2. Busque el servicio EC2 y en el menú izquierdo entre a Instances.
3. Marque su instancia y abra la pestaña Security. Haga clic en el enlace del grupo de seguridad (se ve como `sg-0123...`).
4. En la página del grupo, pestaña Inbound rules, botón Edit inbound rules.
5. Add rule. Type: HTTP. Port range: 80 (se llena solo). Source: Anywhere-IPv4 (`0.0.0.0/0`).
6. Save rules.

No abra el puerto 8000: la evidencia de aislamiento necesita que desde internet no se pueda llegar a Django. Si en el Tutorial 4 abrió el 8000, elimine esa regla (Edit inbound rules, botón Remove en esa fila, Save rules). Mantenga el puerto 22 (SSH), o ya no podrá entrar.

### B.6 Prueba rápida desde la EC2

```bash
curl -i http://localhost/inventario/
```

Debe responder `HTTP/1.1 200 OK` con el HTML del inventario.

## Parte C: las tres capturas que pide el enunciado

### Captura 1: Evidencia de Enrutamiento (navegador)

URL exacta: `http://<IP-EC2>/api/v1/comprar/`

La URL no debe llevar `:8000`. Escriba `http://` explícito: algunos navegadores pueden intentar `https://` y no responde (Nginx solo escucha en el 80).

Esta ruta solo acepta POST (es la API de compra). Un navegador hace un GET, así que la respuesta esperada es un error 405, y es correcto: prueba que la petición pasó por Nginx, llegó a Gunicorn y Django respondió. En la pantalla debe ver la interfaz de Django REST framework con:

- el título "Compra Api" y la barra negra de Django REST framework;
- la línea `HTTP 405 Method Not Allowed`;
- `Allow: POST, OPTIONS`;
- el cuerpo `{ "detail": "Method \"GET\" not allowed." }`;
- abajo, una caja "Content" con un botón POST.

En la captura debe verse la barra de direcciones completa con la IP y sin el puerto.

Para que la captura muestre "consumiendo la API" y no solo el error, tome una segunda captura (recomendada) en esa misma página: en la caja "Content" pegue este JSON y presione el botón POST:

```json
{
  "libro_id": 1,
  "direccion_envio": "Calle 123 #45-67, Medellin"
}
```

La página se recarga mostrando `HTTP 201 Created` y `"estado": "exito"` con el mensaje `Orden creada. Total: 178.50`. Entregue las dos capturas (el 405 y el 201).

Como refuerzo, `http://<IP-EC2>/api/v1/productos/` (GET) debe mostrar la lista JSON de libros con su `stock_actual`, y el libro 1 habrá bajado una unidad.

### Captura 2: Evidencia de Aislamiento (terminal local)

Desde su computador, no desde la EC2, intente llegar a Django por el puerto 8000:

```bash
curl -m 10 http://<IP-EC2>:8000/
```

Resultado esperado: tras 10 segundos, `curl: (28) Connection timed out after 10001 milliseconds` (o similar). En Windows PowerShell use `curl.exe -m 10 http://<IP-EC2>:8000/`, o bien:

```powershell
Test-NetConnection <IP-EC2> -Port 8000
```

que debe decir `TcpTestSucceeded : False`. También sirve abrir `http://<IP-EC2>:8000` en el navegador y capturar la pantalla de "no se puede acceder" (timeout). La captura debe mostrar el comando y el resultado.

Nota técnica: el timeout se da porque el Security Group no deja pasar el 8000. Si en su grupo hubiera esa regla abierta, en lugar de timeout vería "Connection refused", porque igualmente no hay nada publicado en ese puerto. En ambos casos Django está aislado; para obtener el timeout que pide el enunciado, deje el 8000 cerrado.

Prueba complementaria dentro de la EC2 (opcional): `curl -m 5 http://localhost:8000/` también falla, porque el contenedor `web` no publica puertos en el host. Y `docker port <carpeta>-web-1` no imprime nada.

### Captura 3: Evidencia de Orquestación (terminal AWS)

En la sesión SSH de la EC2:

```bash
docker ps
```

Deben verse los tres contenedores con `STATUS` que empieza por `Up`: nginx (imagen `nginx:1.25-alpine`, puertos `0.0.0.0:80->80/tcp`), web (imagen de su proyecto, comando `gunicorn Tienda.wsgi:...`, puertos solo `8000/tcp`, sin flecha, lo que significa que no está publicado) y db (`postgres:15`, `Up ... (healthy)`).

La salida de `docker ps` es ancha y puede partirse en varias líneas. Reduzca el tamaño de letra o ensanche la ventana hasta que cada contenedor quede en una sola línea. Si aun así no se lee, use esta versión compacta (lista los mismos contenedores):

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

Como refuerzo, `docker compose logs nginx` muestra las peticiones que hizo a la API (líneas con `GET /api/v1/comprar/ ... 405` y `POST /api/v1/comprar/ ... 201`).

## Problemas frecuentes

**502 Bad Gateway.** Nginx está arriba pero no logra hablar con Django. Mire `docker ps`: si `web` no está `Up` (o se reinicia), lea por qué con `docker compose logs web`. Si `web` está bien, reinicie Nginx para que vuelva a resolver al backend: `docker compose restart nginx`.

**404 o "Not Found" en una ruta que sí existe.** Confirme que escribió la URL completa con la barra final: `/api/v1/comprar/`, `/api/v1/productos/`, `/inventario/`.

**El navegador no carga nada (se queda esperando).** Casi siempre es el Security Group sin la regla HTTP 80 (parte B.5), o la IP de la EC2 cambió tras reiniciar el laboratorio. Revise la IP en la consola y pruebe `curl -i http://localhost/inventario/` dentro de la EC2: si ahí funciona, el problema es el firewall o la IP.

**Cambié `nginx.conf` y no se ve el cambio.** Nginx lee su configuración al arrancar. Después de un `git pull` que modifique `nginx/nginx.conf`, ejecute `docker compose restart nginx`. Use `restart` y no `nginx -s reload`: git reemplaza el archivo por uno nuevo y el contenedor puede seguir viendo el viejo hasta que se reinicia. Un `docker compose up -d --build` tampoco recrea Nginx si solo cambió ese archivo y el compose quedó igual.

**Django responde 500 o dice que no existe la tabla `tienda_app_libro`.** Faltó el paso B.4: corra `migrate` y `preparar_datos` dentro del contenedor `web`.

**Django responde 400 "DisallowedHost" (Invalid HTTP_HOST header).** El compose ya define `DJANGO_ALLOWED_HOSTS=*`. Si lo quitó, Django rechaza la IP de la EC2. Vuelva a ponerlo o liste su IP.

**`web` se cae al arrancar con "connection refused" a `db`.** Postgres todavía no estaba listo. El compose de esta carpeta ya espera con un chequeo de salud (`healthcheck`), así que no debería pasar. Si usa un compose antiguo sin ese chequeo, corra otra vez `docker compose up -d` cuando `db` esté `Up`.

**`permission denied` al usar docker.** Use `sudo docker ...`, o agréguese al grupo: `sudo usermod -aG docker $USER` y vuelva a entrar por SSH.

**La página de DRF se ve sin colores.** Falta `whitenoise` en `requirements.txt` o la imagen quedó vieja: `docker compose up -d --build`.

## Al terminar: no gaste créditos

- Bajar los contenedores (conserva los datos de la base): `docker compose down`.
- Bajar todo y borrar la base, el volumen y las imágenes construidas: `docker compose down -v --rmi local`.
- Regrese al Learner Lab y detenga la instancia (EC2, Instances, Instance state, Stop instance) o use End Lab. Una EC2 encendida sigue gastando créditos aunque no la use.
- Si tiene la base RDS del tutorial anterior y ya no la necesita, bórrela desde la consola de RDS. Una RDS consume créditos mientras exista.
- Las capturas son de usted: revise que ninguna muestre llaves, tokens ni contraseñas reales antes de entregarlas.
