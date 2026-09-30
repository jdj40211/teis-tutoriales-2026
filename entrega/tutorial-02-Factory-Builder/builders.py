from decimal import Decimal

from ..models import Orden
from .logic import CalculadorImpuestos


class OrdenBuilder:
    """
    Builder: arma una Orden paso a paso y valida antes de crearla.
    Toda la lógica de cálculo (subtotal, IVA, total) queda aquí encapsulada,
    así la vista y el servicio no vuelven a calcular nada.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._items = []
        self._direccion = ""

    def con_usuario(self, usuario):
        # El usuario es opcional: sin login la orden queda como compra de invitado.
        self._usuario = usuario
        return self  # Permite Fluent Interface

    def con_productos(self, productos):
        """Recibe una lista de Libro; un libro repetido cuenta como más unidades."""
        self._items = list(productos)
        return self

    def para_envio(self, direccion):
        self._direccion = direccion
        return self

    def build(self) -> Orden:
        if not self._items:
            raise ValueError("Datos insuficientes para crear la orden.")

        # Encapsulamos la lógica de cálculo: el subtotal se suma aquí y el IVA
        # (con su redondeo a centavos) lo decide CalculadorImpuestos.
        subtotal = sum((Decimal(str(p.precio)) for p in self._items), Decimal("0"))
        total = CalculadorImpuestos.obtener_total_con_iva(subtotal)

        orden = Orden.objects.create(
            usuario=self._usuario,
            libro=self._items[0],  # el modelo Orden guarda un solo libro principal
            total=total,
            direccion_envio=self._direccion,
        )
        self.reset()
        return orden
