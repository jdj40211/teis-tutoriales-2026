# 🚀 Django Clean Monolith: De Spaghetti a Grado Empresarial

Este proyecto es una guía práctica para transformar una aplicación de Django tradicional en un sistema con arquitectura de capas, siguiendo principios de ingeniería de software utilizados en consultoría de alto nivel.

---

## 🏗️ Resumen de la Arquitectura

Hemos separado las responsabilidades para evitar el antipatrón de la "Vista Gorda" (Fat View), organizando el código en las siguientes capas:

| Capa | Ubicación | Responsabilidad |
| :--- | :--- | :--- |
| **Presentación** | `views.py` | Recibir Requests, delegar al servicio y retornar Responses (HTML/JSON). |
| **Servicio** | `services.py` | Orquestar el flujo de negocio. Es el "Cerebro" que conecta el dominio con los datos. |
| **Dominio** | `domain/` | Contiene la lógica pura (Impuestos, validaciones) e interfaces (Contratos). |
| **Infraestructura** | `infra/` | Implementaciones técnicas externas (Pasarelas de pago, logs, APIs). |
| **Datos** | `models.py` | Definición de tablas y persistencia mediante el ORM de Django. |



---

## 🛡️ Principios SOLID Aplicados

1. **S - Single Responsibility:** Cada clase tiene una sola razón para existir. El `CalculadorImpuestos` no sabe de bases de datos; la `View` no sabe de impuestos.
2. **O - Open/Closed:** El sistema está abierto a nuevas reglas de negocio (ej. nuevos impuestos) sin necesidad de modificar el flujo principal de compra.
3. **L - Liskov Substitution:** Podemos intercambiar el `BancoNacionalProcesador` por cualquier otro procesador que siga la interfaz `ProcesadorPago`.
4. **I - Interface Segregation:** Las interfaces en `domain/interfaces.py` son específicas y minimalistas.
5. **D - Dependency Inversion:** La capa de servicio no depende de una implementación de banco concreta, sino de una abstracción (Interfaz).

---

## 🛠️ Instalación y Configuración

Siga estos pasos para poner en marcha el entorno local:

### 1. Clonar y Preparar Entorno
```bash
git clone [https://github.com/tu-usuario/django-clean-monolith.git](https://github.com/tu-usuario/django-clean-monolith.git)
cd django-clean-monolith
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 2. Base de datos
```bash
python manage.py migrate
```

### 3. Crear datos de prueba
El comando `preparar_datos` aplica las migraciones y crea cuatro libros con stock
(entre ellos "Clean Code en Python" a 150.0 con 10 unidades). Se puede repetir sin
duplicar datos.
```bash
python manage.py preparar_datos
# Para volver al stock inicial y borrar las órdenes:
python manage.py preparar_datos reiniciar
```
(Si prefiere hacerlo a mano, el shell de Django sirve con
`from tienda_app.models import Libro, Inventario`; la app se llama `tienda_app`.)

### 4. Ejecutar
```bash
python manage.py runserver
```

## 📂 Estructura de Archivos (App: tienda_app)
```
tienda_app/
├── api/              # Puerta JSON (Django REST Framework)
│   ├── views.py      # CompraAPIView (POST /api/v1/comprar/) y ProductoListAPIView (GET /api/v1/productos/)
│   └── serializers.py # Serializers: LibroSerializer y OrdenInputSerializer
├── domain/           # Lógica pura e Interfaces
│   ├── logic.py      # SRP: Cálculo de IVA
│   ├── interfaces.py # DIP: Contrato de Pago
│   └── builders.py   # Builder Pattern para el objeto complejo Orden
├── infra/            # Detalles técnicos
│   ├── gateways.py   # Implementación de Banco (Log local con el nombre del estudiante)
│   └── factories.py  # Factory Method para generación de procesadores (PAYMENT_PROVIDER)
├── management/commands/preparar_datos.py  # Migra y crea los libros de prueba
├── services.py       # Capa de Servicio (Orquestación)
├── views.py          # Class-Based Views (Compra, Compra Rápida e Inventario)
├── models.py         # Modelos de Django
└── tests/            # Pruebas: python manage.py test
```

## Rutas

- `/` y `/inventario/`: página HTML con el inventario.
- `/compra/<id>/`: compra (HTML).
- `/compra-rapida/<id>/`: compra rápida (HTML).
- `/api/v1/comprar/`: POST JSON, por ejemplo `{"libro_id": 1, "direccion_envio": "Calle 123"}`.
- `/api/v1/productos/`: GET JSON con la lista de libros y su `stock_actual`.

## Pruebas y configuración

```bash
python manage.py test
PAYMENT_PROVIDER=MOCK python manage.py runserver   # pagos simulados, sin log
```

En `entrega/` hay una carpeta por tutorial con los archivos de entrega y la guía para
generar la evidencia. `NOTAS-INCONSISTENCIAS.md` explica lo que hubo que ajustar respecto a los PDF.

## Docker, Nginx y Gunicorn (Tutorial 5)

La arquitectura de tres contenedores (`nginx`, `web` con Gunicorn y `db` con PostgreSQL) se levanta así:

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py preparar_datos
```

Nginx escucha en el puerto 80 del equipo y es el único que publica puertos; Django (`web`) solo es
alcanzable desde la red interna de Docker. La base de datos se elige con las variables
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`; sin `DB_HOST` se usa SQLite.
La guía para la EC2 está en `entrega/tutorial-05-Strangler-Nginx/GUIA-DESPLIEGUE-AWS.md`.
Las decisiones y los huecos de los enunciados están en `NOTAS-TUTORIALES-5-6.md`.

## Strangler Pattern: Django (v1) y Flask (v2) detrás de Nginx (Tutorial 6)

`microservicio_pagos/` contiene el microservicio Flask que atiende `POST /api/v2/comprar`.
Nginx manda `/api/v1/` y la ruta raíz a Django (`web_django`) y `/api/v2/comprar` a Flask (`pagos_flask`).

```bash
docker compose up -d --build --remove-orphans
docker compose restart nginx
docker compose logs nginx   # cada línea dice backend=django_v1 o backend=flask_v2
```

La guía para la EC2 está en `entrega/tutorial-06-Flask-101/GUIA-DESPLIEGUE-AWS.md`.
