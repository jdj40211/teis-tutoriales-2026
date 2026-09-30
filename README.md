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
├── domain/           # Lógica pura e Interfaces
│   ├── logic.py      # SRP: Cálculo de IVA
│   └── interfaces.py # DIP: Contrato de Pago
├── infra/            # Detalles técnicos
│   └── gateways.py   # Implementación de Banco (Log local)
├── services.py       # Capa de Servicio (Orquestación)
├── views.py          # Class-Based Views
└── models.py         # Modelos de Django

