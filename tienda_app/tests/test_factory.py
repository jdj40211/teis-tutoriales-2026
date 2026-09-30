import io
import os
from contextlib import redirect_stdout
from unittest import mock

from django.test import SimpleTestCase

from tienda_app.domain.interfaces import ProcesadorPago
from tienda_app.infra.factories import MockPaymentProcessor, PaymentFactory
from tienda_app.infra.gateways import ARCHIVO_LOG, BancoNacionalProcesador

from .base import LogTemporalMixin


class PaymentFactoryTests(LogTemporalMixin, SimpleTestCase):
    def test_sin_variable_entrega_el_banco_real(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("PAYMENT_PROVIDER", None)
            procesador = PaymentFactory.get_processor()
        self.assertIsInstance(procesador, BancoNacionalProcesador)

    def test_con_mock_entrega_el_procesador_falso(self):
        with mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}):
            procesador = PaymentFactory.get_processor()
        self.assertIsInstance(procesador, MockPaymentProcessor)

    def test_un_valor_desconocido_cae_en_el_banco_real(self):
        with mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "PAYPAL"}):
            self.assertIsInstance(PaymentFactory.get_processor(), BancoNacionalProcesador)

    def test_ambos_procesadores_cumplen_el_contrato(self):
        self.assertIsInstance(MockPaymentProcessor(), ProcesadorPago)
        self.assertIsInstance(BancoNacionalProcesador(), ProcesadorPago)

    def test_el_mock_imprime_el_debug_y_no_escribe_el_log(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            resultado = MockPaymentProcessor().pagar(178.5)
        self.assertTrue(resultado)
        self.assertIn("[DEBUG] Mock Payment", salida.getvalue())
        self.assertIn("178.5", salida.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.carpeta_log, ARCHIVO_LOG)))
