from collections import Counter

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro, Orden


class CompraService:
    """
    SERVICE LAYER: Orquesta la interacción entre el dominio,
    la infraestructura y la base de datos.
    """

    def __init__(self, procesador_pago):
        # Inyectamos la dependencia (DIP): el servicio no sabe qué banco es
        self.procesador_pago = procesador_pago
        self.builder = OrdenBuilder()

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def ejecutar_proceso_compra(self, usuario, lista_productos, direccion):
        """Tutorial 2: compra de una lista de libros. Devuelve un mensaje de éxito."""
        orden = self._procesar_orden(usuario, lista_productos, direccion)
        return f"Orden {orden.id} procesada exitosamente."

    def ejecutar_compra(self, libro_id, cantidad=1, direccion="", usuario=None):
        """
        Compra de un libro por id. La usan la vista HTML y la API (Tutorial 3).
        Devuelve el total cobrado.
        """
        libro = get_object_or_404(Libro, id=libro_id)
        orden = self._procesar_orden(usuario, [libro] * cantidad, direccion)
        return orden.total

    def _procesar_orden(self, usuario, lista_productos, direccion):
        """Flujo común: validar stock, construir la orden, descontar el inventario y cobrar."""
        unidades = self._validar_stock(lista_productos)

        # Todo ocurre en una transacción: si el pago falla (o lanza un error) se
        # deshacen la orden y el descuento de inventario.
        with transaction.atomic():
            # Uso del Builder: semántica clara y validación interna
            orden = (
                self.builder
                .con_usuario(usuario)
                .con_productos(lista_productos)
                .para_envio(direccion)
                .build()
            )
            self._descontar_inventario(unidades)

            # Uso del Factory (inyectado): cambia el comportamiento sin cambiar código
            if not self.procesador_pago.pagar(orden.total):
                raise Exception("La transacción fue rechazada por el banco.")
        return orden

    def _validar_stock(self, lista_productos):
        """Revisa que alcance el inventario de cada libro. Devuelve {libro_id: unidades}."""
        unidades = Counter(libro.id for libro in lista_productos)
        titulos = {libro.id: libro.titulo for libro in lista_productos}
        for libro_id, cantidad in unidades.items():
            inv = Inventario.objects.filter(libro_id=libro_id).first()
            disponible = inv.cantidad if inv else 0  # sin registro de inventario = sin stock
            if disponible < cantidad:
                raise ValueError(
                    f"No hay suficiente stock de '{titulos[libro_id]}' para completar la compra."
                )
        return unidades

    def _descontar_inventario(self, unidades):
        for libro_id, cantidad in unidades.items():
            # El filtro cantidad__gte evita dejar el stock en negativo si otra compra
            # se llevó las unidades entre la validación y este descuento.
            filas = Inventario.objects.filter(libro_id=libro_id, cantidad__gte=cantidad).update(
                cantidad=F("cantidad") - cantidad
            )
            if not filas:
                raise ValueError("El stock cambió mientras se procesaba la compra, intente de nuevo.")


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
