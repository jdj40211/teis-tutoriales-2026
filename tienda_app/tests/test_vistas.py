import io
import os
from contextlib import redirect_stdout
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from tienda_app.infra.gateways import ARCHIVO_LOG
from tienda_app.models import Inventario, Orden

from .base import LogTemporalMixin, ProcesadorFalso, crear_libro


class CompraRapidaViewTests(LogTemporalMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.libro = crear_libro(cantidad=1)
        self.url = reverse("compra_rapida", args=[self.libro.id])

    def test_get_muestra_libro_y_total_con_iva(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Clean Code en Python")
        self.assertContains(respuesta, "178.5")
        self.assertTemplateUsed(respuesta, "tienda_app/compra_rapida.html")

    def test_get_de_libro_inexistente_es_404(self):
        self.assertEqual(self.client.get(reverse("compra_rapida", args=[999])).status_code, 404)

    def test_post_compra_y_descuenta_inventario(self):
        respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Compra exitosa")
        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 0)
        self.assertEqual(Orden.objects.count(), 1)

    def test_post_sin_stock_responde_400(self):
        self.client.post(self.url)  # consume la única unidad
        respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 400)
        self.assertContains(respuesta, "No hay existencias", status_code=400)

    def test_post_con_pago_rechazado_responde_402_y_no_descuenta(self):
        rechazo = ProcesadorFalso(resultado=False)
        with mock.patch("tienda_app.views.PaymentFactory.get_processor", return_value=rechazo):
            respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 402)
        self.assertContains(respuesta, "rechazó el pago", status_code=402)
        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 1)
        self.assertEqual(Orden.objects.count(), 0)


class CompraViewTests(LogTemporalMixin, TestCase):
    """CompraView del repo base, ahora con el procesador elegido por la fábrica."""

    def setUp(self):
        super().setUp()
        self.libro = crear_libro(cantidad=1)
        self.url = reverse("finalizar_compra", args=[self.libro.id])

    def test_get_muestra_el_detalle(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Clean Code en Python")
        self.assertTemplateUsed(respuesta, "tienda_app/compra.html")

    def test_post_con_mock_imprime_el_debug_y_compra(self):
        salida = io.StringIO()
        with mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}), redirect_stdout(salida):
            respuesta = self.client.post(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Gracias por su compra")
        self.assertIn("[DEBUG] Mock Payment", salida.getvalue())
        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 0)
        self.assertEqual(Orden.objects.count(), 1)
        # El Mock no toca el log del banco
        self.assertEqual(os.listdir(self.carpeta_log), [])

    def test_post_sin_la_variable_usa_el_banco_y_escribe_el_log(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("PAYMENT_PROVIDER", None)
            respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(os.listdir(self.carpeta_log), [ARCHIVO_LOG])

    def test_post_sin_stock_responde_400(self):
        with mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}), redirect_stdout(io.StringIO()):
            self.client.post(self.url)
            respuesta = self.client.post(self.url)
        self.assertEqual(respuesta.status_code, 400)
        self.assertContains(respuesta, "No hay suficiente stock", status_code=400)

    def test_post_de_un_libro_inexistente_responde_404(self):
        self.assertEqual(self.client.post(reverse("finalizar_compra", args=[9999])).status_code, 404)

    def test_la_compra_rapida_tambien_usa_la_fabrica(self):
        salida = io.StringIO()
        with mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}), redirect_stdout(salida):
            respuesta = self.client.post(reverse("compra_rapida", args=[self.libro.id]))
        self.assertContains(respuesta, "Compra exitosa")
        self.assertIn("[DEBUG] Mock Payment", salida.getvalue())
