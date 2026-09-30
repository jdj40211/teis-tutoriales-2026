# Imagen del microservicio de pagos (Flask, v2). Aquí alpine sirve: Flask y
# Gunicorn son Python puro y no necesitan compilar nada.
FROM python:3.11-alpine
WORKDIR /app
RUN pip install flask gunicorn
COPY . .
EXPOSE 5000
# 'app:app' = archivo app.py, variable app. Se asocia a todas las interfaces
# del contenedor para que Nginx pueda llegar por la red de Docker.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
