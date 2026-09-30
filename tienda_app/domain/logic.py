from decimal import ROUND_HALF_UP, Decimal


class CalculadorImpuestos:
    """
    S: Responsabilidad única - Solo calcula impuestos.
    O: Abierto a extensión - Podríamos heredar para diferentes países.
    """
    @staticmethod
    def obtener_total_con_iva(precio_base) -> Decimal:
        IVA = Decimal("1.19")  # Regla de negocio pura
        # Se calcula con Decimal y se redondea a centavos: con float el total
        # podía salir como 249.89999999999998 en pantalla y en el log.
        total = Decimal(str(precio_base)) * IVA
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
