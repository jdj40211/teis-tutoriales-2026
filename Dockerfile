# Imagen de la aplicación Django (Tutorial 4).
# Se usa python:3.11-slim y no alpine: psycopg2-binary no publica ruedas para
# musl (alpine), así que en alpine habría que compilar psycopg2 con gcc y libpq-dev.
FROM python:3.11-slim

# No generar .pyc y mostrar los logs de Python al instante en docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias: si requirements.txt no cambia, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copia los estáticos a una carpeta fuera de /app (el compose monta .:/app encima de /app)
ENV STATIC_ROOT=/opt/staticfiles
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Por defecto, el servidor de desarrollo. El Tutorial 5 lo cambia por Gunicorn desde el compose.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
