"""Utilidades compartidas por las pruebas."""
import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings

from tienda_app.domain.interfaces import ProcesadorPago
from tienda_app.models import Inventario, Libro


class ProcesadorFalso(ProcesadorPago):
    """Procesador de pago de prueba: guarda los montos y responde lo que le pidamos."""

    def __init__(self, resultado=True):
        self.resultado = resultado
        self.montos = []

    def pagar(self, monto):
        self.montos.append(monto)
        return self.resultado


class LogTemporalMixin:
    """
    Redirige el log del BancoNacionalProcesador a una carpeta temporal para que
    ninguna prueba escriba el archivo real en la raíz del proyecto.
    """

    def setUp(self):
        super().setUp()
        # Las pruebas no dependen de lo que tenga exportado la terminal:
        # sin PAYMENT_PROVIDER la fábrica entrega el banco real.
        entorno = mock.patch.dict(os.environ)
        entorno.start()
        self.addCleanup(entorno.stop)
        os.environ.pop("PAYMENT_PROVIDER", None)
        self.carpeta_log = tempfile.mkdtemp(prefix="pagos_test_")
        self.addCleanup(shutil.rmtree, self.carpeta_log, ignore_errors=True)
        configuracion = override_settings(PAGOS_LOG_DIR=self.carpeta_log)
        configuracion.enable()
        self.addCleanup(configuracion.disable)


def crear_libro(titulo="Clean Code en Python", precio="150.00", cantidad=10):
    libro = Libro.objects.create(titulo=titulo, precio=precio)
    Inventario.objects.create(libro=libro, cantidad=cantidad)
    return libro
