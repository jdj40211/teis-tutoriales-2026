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
