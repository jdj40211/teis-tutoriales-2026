# Tutorial 1: Resumen de código

Estudiante: Juan David Sierra Orozco
Materia: Tópicos Especiales en Ingeniería de Software (EAFIT)
Asignación: tutorial01-DjangoSOLID

Este documento reúne el código de `tienda_app/services.py` y `tienda_app/views.py` para mostrar que la lógica de la Compra Rápida salió de la capa de presentación. Las clases del tutorial son `CompraRapidaService` (en `services.py`) y `CompraRapidaView` (en `views.py`). `CompraService` y `CompraView` vienen del repo base del profesor y se usan en el Tutorial 2; conviven en los mismos archivos pero no se llaman entre sí.

## Dónde quedó cada responsabilidad

La vista `CompraRapidaView` solo traduce entre HTTP y el servicio: arma el servicio, llama a `procesar` y elige la plantilla y el código de estado (200, 400 o 402), con menos de 10 líneas por método (SRP). El servicio `CompraRapidaService` concentra la orquestación: valida el stock, pide el total a `CalculadorImpuestos`, cobra y descuenta el inventario. El IVA vive en `domain/logic.py`, así que cambiar la regla de impuestos no toca ni la vista ni el flujo de compra (OCP). El servicio recibe el procesador de pago por el constructor y solo conoce la interfaz `ProcesadorPago` de `domain/interfaces.py` (DIP), por eso cualquier banco que la cumpla lo reemplaza sin cambios (LSP), y la interfaz tiene un único método, `pagar` (ISP). El banco concreto, `BancoNacionalProcesador`, está en `infra/gateways.py` y es el único que sabe que los pagos se escriben en el archivo `pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log`.

## services.py

```python
from django.shortcuts import get_object_or_404
from .models import Libro, Inventario, Orden
from .domain.logic import CalculadorImpuestos

class CompraService:
    """
    SERVICE LAYER: Orquesta la interacción entre el dominio, 
    la infraestructura y la base de datos.
    """
    def __init__(self, procesador_pago):
        # Inyectamos la dependencia (DIP)
        self.procesador_pago = procesador_pago

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def ejecutar_compra(self, libro_id, cantidad):
        # 1. Obtener datos
        libro = get_object_or_404(Libro, id=libro_id)
        inv = get_object_or_404(Inventario, libro=libro)

        # 2. Validar Reglas de Negocio
        if inv.cantidad < cantidad:
            raise ValueError("No hay suficiente stock para completar la compra.")

        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)

        # 3. Procesar Infraestructura (Pago)
        pago_exitoso = self.procesador_pago.pagar(total)
        
        if not pago_exitoso:
            raise Exception("La transacción fue rechazada por el banco.")

        # 4. Persistencia de efectos secundarios
        inv.cantidad -= cantidad
        inv.save()
        
        Orden.objects.create(libro=libro, total=total)
        
        return total


class CompraRapidaService:
    """
    Tutorial 1, Paso 3: el caso de uso de la "Compra Rápida" extraído de la vista.
    Aquí vive la orquestación (inventario, impuestos, pago). La vista solo
    recibe el request y devuelve la respuesta.
    """

    def __init__(self, procesador_pago):
        # DIP: dependemos de la interfaz ProcesadorPago, no de un banco concreto
        self.procesador_pago = procesador_pago

    def obtener_detalle(self, libro_id):
        """Datos para mostrar en el GET: el libro y su total estimado con IVA."""
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def procesar(self, libro_id):
        """
        Compra de una unidad. Devuelve el total cobrado, o None si el
        procesador de pago rechazó la transacción.
        Lanza ValueError cuando no hay existencias.
        """
        libro = get_object_or_404(Libro, id=libro_id)
        inv = Inventario.objects.filter(libro=libro).first()

        # Un libro sin registro de inventario cuenta como sin existencias
        if inv is None or inv.cantidad <= 0:
            raise ValueError("No hay existencias.")

        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)

        if self.procesador_pago.pagar(total):
            inv.cantidad -= 1
            inv.save()
            # La FBV original también dejaba la Orden registrada
            Orden.objects.create(libro=libro, total=total)
            return total
        return None
```

## views.py

```python
from django.views import View
from django.shortcuts import render, HttpResponse
from .services import CompraRapidaService, CompraService
from .infra.gateways import BancoNacionalProcesador

class CompraView(View):
    """
    CBV: Vista Basada en Clases. 
    Actúa como un "Portero": recibe la petición y delega al servicio.
    """
    template_name = 'tienda_app/compra.html'
    
    # Configuramos el servicio con su implementación de infraestructura
    def setup_service(self):
        gateway = BancoNacionalProcesador()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.ejecutar_compra(libro_id, cantidad=1)
            return render(request, self.template_name, {
                'mensaje_exito': f"¡Gracias por su compra! Total: ${total}",
                'total': total
            })
        except (ValueError, Exception) as e:
            # Manejo de errores de negocio transformados a respuesta de usuario
            return render(request, self.template_name, {
                'error': str(e)
            }, status=400)


class CompraRapidaView(View):
    """
    Tutorial 1: la vista queda como un puente entre la web y el servicio.
    Cada método tiene menos de 10 líneas y ninguna regla de negocio.
    """

    template_name = 'tienda_app/compra_rapida.html'

    def setup_service(self):
        return CompraRapidaService(procesador_pago=BancoNacionalProcesador())

    def get(self, request, libro_id):
        contexto = self.setup_service().obtener_detalle(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.procesar(libro_id)
        except ValueError as error:
            return render(request, self.template_name, {'error': str(error)}, status=400)
        if total is None:
            return render(request, self.template_name, {'error': 'El banco rechazó el pago.'}, status=402)
        return render(request, self.template_name, {'mensaje_exito': f'Compra exitosa. Total: ${total}'})
```
