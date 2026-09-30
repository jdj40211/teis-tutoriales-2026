import os

from ..domain.interfaces import ProcesadorPago
from .gateways import BancoNacionalProcesador


# Implementación ligera para pruebas (Mocking). Hereda de ProcesadorPago para
# cumplir el mismo contrato que el banco real (Liskov).
class MockPaymentProcessor(ProcesadorPago):
    def pagar(self, monto: float) -> bool:
        print(f"[DEBUG] Mock Payment: Procesando pago de ${monto} sin cargo real.")
        return True


class PaymentFactory:
    """
    Factory Method: decide qué procesador de pago usar según la configuración
    del ambiente, así ni las vistas ni los servicios eligen el banco.
    """

    @staticmethod
    def get_processor() -> ProcesadorPago:
        # LECCIÓN DE ARQUITECTURA: la configuración viene del ambiente, no del código
        provider = os.getenv('PAYMENT_PROVIDER', 'BANCO')

        if provider == 'MOCK':
            return MockPaymentProcessor()

        # Por defecto usamos la infraestructura real
        return BancoNacionalProcesador()
