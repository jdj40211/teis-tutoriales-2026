from decimal import Decimal

from django.http import Http404
from django.test import TestCase

from tienda_app.models import Inventario, Orden
from tienda_app.services import CompraRapidaService

from .base import ProcesadorFalso, crear_libro


class CompraRapidaServiceTests(TestCase):
    """El servicio se prueba con un procesador de pago falso, sin banco real."""

    def setUp(self):
        self.libro = crear_libro(cantidad=2)

    def test_compra_exitosa_cobra_con_iva_y_descuenta_stock(self):
        procesador = ProcesadorFalso(resultado=True)
        servicio = CompraRapidaService(procesador_pago=procesador)

        total = servicio.procesar(self.libro.id)

        self.assertEqual(total, Decimal("178.50"))
        self.assertEqual(procesador.montos, [Decimal("178.50")])
        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 1)
        orden = Orden.objects.get()
        self.assertEqual(orden.libro, self.libro)
        self.assertEqual(orden.total, Decimal("178.50"))

    def test_sin_stock_lanza_value_error_y_no_cobra(self):
        Inventario.objects.filter(libro=self.libro).update(cantidad=0)
        procesador = ProcesadorFalso()
        servicio = CompraRapidaService(procesador_pago=procesador)

        with self.assertRaises(ValueError):
            servicio.procesar(self.libro.id)

        self.assertEqual(procesador.montos, [])
        self.assertEqual(Orden.objects.count(), 0)

    def test_pago_fallido_devuelve_none_y_no_toca_inventario(self):
        servicio = CompraRapidaService(procesador_pago=ProcesadorFalso(resultado=False))

        self.assertIsNone(servicio.procesar(self.libro.id))

        self.assertEqual(Inventario.objects.get(libro=self.libro).cantidad, 2)
        self.assertEqual(Orden.objects.count(), 0)

    def test_libro_sin_registro_de_inventario_cuenta_como_sin_existencias(self):
        Inventario.objects.filter(libro=self.libro).delete()
        procesador = ProcesadorFalso()
        servicio = CompraRapidaService(procesador_pago=procesador)

        with self.assertRaises(ValueError):
            servicio.procesar(self.libro.id)

        self.assertEqual(procesador.montos, [])

    def test_libro_inexistente_lanza_404(self):
        servicio = CompraRapidaService(procesador_pago=ProcesadorFalso())
        with self.assertRaises(Http404):
            servicio.procesar(9999)

    def test_detalle_para_el_get(self):
        servicio = CompraRapidaService(procesador_pago=ProcesadorFalso())
        detalle = servicio.obtener_detalle(self.libro.id)
        self.assertEqual(detalle["libro"], self.libro)
        self.assertEqual(detalle["total"], Decimal("178.50"))
