from collections import Counter
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase

from tienda_app.models import Inventario, Orden
from tienda_app.services import CompraService

from .base import ProcesadorFalso, crear_libro


class CompraServiceTests(TestCase):
    """CompraService con procesador falso: Builder + Factory inyectada."""

    def setUp(self):
        self.libro = crear_libro(cantidad=3)
        self.otro = crear_libro(titulo="Arquitectura Limpia", precio="250.00", cantidad=1)

    def stock(self, libro):
        return Inventario.objects.get(libro=libro).cantidad

    def test_ejecutar_proceso_compra_exitoso(self):
        procesador = ProcesadorFalso()
        servicio = CompraService(procesador_pago=procesador)
        usuario = get_user_model().objects.create_user("juan", password="x")

        mensaje = servicio.ejecutar_proceso_compra(usuario, [self.libro, self.otro], "Calle 123")

        orden = Orden.objects.get()
        self.assertEqual(mensaje, f"Orden {orden.id} procesada exitosamente.")
        self.assertEqual(orden.usuario, usuario)
        self.assertEqual(orden.direccion_envio, "Calle 123")
        self.assertEqual(orden.total, Decimal("476.00"))
        self.assertEqual(len(procesador.montos), 1)
        self.assertEqual(self.stock(self.libro), 2)
        self.assertEqual(self.stock(self.otro), 0)

    def test_ejecutar_compra_devuelve_el_total_y_descuenta(self):
        servicio = CompraService(procesador_pago=ProcesadorFalso())
        total = servicio.ejecutar_compra(self.libro.id, cantidad=2, direccion="Calle 9")
        self.assertEqual(total, Decimal("357.00"))
        self.assertEqual(self.stock(self.libro), 1)
        self.assertEqual(Orden.objects.get().direccion_envio, "Calle 9")

    def test_sin_stock_lanza_value_error_sin_cobrar_ni_crear_orden(self):
        procesador = ProcesadorFalso()
        servicio = CompraService(procesador_pago=procesador)

        with self.assertRaises(ValueError):
            servicio.ejecutar_compra(self.otro.id, cantidad=2)

        self.assertEqual(procesador.montos, [])
        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(self.stock(self.otro), 1)

    def test_stock_insuficiente_en_uno_de_varios_libros_cancela_todo(self):
        servicio = CompraService(procesador_pago=ProcesadorFalso())
        with self.assertRaises(ValueError):
            servicio.ejecutar_proceso_compra(None, [self.libro, self.otro, self.otro], "")
        self.assertEqual(self.stock(self.libro), 3)
        self.assertEqual(self.stock(self.otro), 1)

    def test_pago_fallido_borra_la_orden_y_no_descuenta(self):
        servicio = CompraService(procesador_pago=ProcesadorFalso(resultado=False))

        with self.assertRaisesMessage(Exception, "rechazada por el banco"):
            servicio.ejecutar_compra(self.libro.id)

        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(self.stock(self.libro), 3)

    def test_lista_vacia_lanza_datos_insuficientes(self):
        servicio = CompraService(procesador_pago=ProcesadorFalso())
        with self.assertRaisesMessage(ValueError, "Datos insuficientes"):
            servicio.ejecutar_proceso_compra(None, [], "Calle 1")

    def test_libro_inexistente_lanza_404(self):
        servicio = CompraService(procesador_pago=ProcesadorFalso())
        with self.assertRaises(Http404):
            servicio.ejecutar_compra(9999)

    def test_detalle_del_producto(self):
        detalle = CompraService(procesador_pago=ProcesadorFalso()).obtener_detalle_producto(self.libro.id)
        self.assertEqual(detalle["libro"], self.libro)
        self.assertEqual(detalle["total"], Decimal("178.50"))

    def test_si_el_banco_lanza_un_error_no_queda_ni_orden_ni_descuento(self):
        class BancoCaido(ProcesadorFalso):
            def pagar(self, monto):
                raise RuntimeError("sin conexión con el banco")

        servicio = CompraService(procesador_pago=BancoCaido())

        with self.assertRaises(RuntimeError):
            servicio.ejecutar_compra(self.libro.id)

        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(self.stock(self.libro), 3)

    def test_libro_sin_registro_de_inventario_cuenta_como_sin_stock(self):
        Inventario.objects.filter(libro=self.libro).delete()
        procesador = ProcesadorFalso()
        servicio = CompraService(procesador_pago=procesador)

        with self.assertRaises(ValueError):
            servicio.ejecutar_compra(self.libro.id)

        self.assertEqual(procesador.montos, [])
        self.assertEqual(Orden.objects.count(), 0)

    def test_si_otra_compra_se_lleva_el_stock_no_se_cobra_ni_se_deja_orden(self):
        # Simulamos la carrera: la validación pasa pero al descontar ya no alcanza.
        procesador = ProcesadorFalso()
        servicio = CompraService(procesador_pago=procesador)

        with mock.patch.object(CompraService, "_validar_stock", return_value=Counter({self.otro.id: 2})):
            with self.assertRaisesMessage(ValueError, "El stock cambió"):
                servicio.ejecutar_proceso_compra(None, [self.otro, self.otro], "")

        self.assertEqual(procesador.montos, [])
        self.assertEqual(Orden.objects.count(), 0)
        self.assertEqual(self.stock(self.otro), 1)
