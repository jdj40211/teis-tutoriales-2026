# Tutorial 2: Puntos para la reflexión

Pregunta del enunciado: por qué el `OrdenBuilder` reduce el riesgo de errores en comparación con crear la orden directamente en la vista.

Esto es solo una lista de ideas de apoyo. La reflexión que se entrega es un párrafo breve que usted debe redactar con sus propias palabras, eligiendo las ideas que mejor pueda explicar y defender.

## Validación centralizada
- Las reglas para que una orden sea válida (hay productos, hay datos mínimos) viven en un solo método, `build()`.
- Si la vista crea la orden a mano, cada vista tiene que acordarse de repetir esas validaciones, y basta olvidarlas en una.
- Nada impide crear una orden vacía o incompleta cuando se usa `Orden.objects.create(...)` suelto en varios sitios; el Builder lo rechaza con un `ValueError` antes de tocar la base de datos.

## Lógica de cálculo encapsulada
- El subtotal, el IVA y el total se calculan dentro del Builder y no en la vista ni en el servicio.
- Si cambia la regla de impuestos, se corrige en un lugar y no hay que buscar todos los sitios donde se instanciaba una `Orden`.
- La vista no puede cobrar mal por un cálculo copiado y desactualizado.

## Interfaz fluida
- `con_usuario(...).con_productos(...).para_envio(...).build()` se lee como un requerimiento de negocio.
- No hay que recordar el orden de muchos parámetros de un constructor largo; cada dato tiene un método con nombre.
- Menos carga cognitiva para quien lee o modifica el código.

## Estado reiniciado después de construir
- `build()` llama a `reset()`, así que los datos de una orden no se filtran a la siguiente.
- Reutilizar el mismo Builder no arrastra el usuario, la dirección ni los productos anteriores.
- Es una fuente de errores sutiles que aparece cuando se arma el objeto con variables sueltas en la vista.

## El objeto solo nace completo
- La `Orden` se crea en un único punto y ya calculada; no existen órdenes a medio llenar guardadas en la base de datos.
- Si la validación falla, no se escribe nada.

## Responsabilidades separadas (SRP)
- La vista se limita a HTTP, el servicio orquesta (stock, cobro, inventario) y el Builder solo sabe cómo construir órdenes.
- Probar el Builder no requiere servidor, bancos ni navegador: basta una prueba unitaria.

## Ideas para conectar con el resto del tutorial
- Relación con la Fábrica: Factory decide qué objeto crear a partir de la configuración; Builder decide cómo armar un objeto complejo paso a paso.
- Por qué el `OrdenBuilder` se pidió en el servicio y no en la vista.
- Un ejemplo concreto de error que evita: orden sin productos, total sin IVA, dirección de otra compra.
