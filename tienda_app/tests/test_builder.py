from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from tienda_app.domain.builders import OrdenBuilder
from tienda_app.models import Orden

from .base import crear_libro


class OrdenBuilderTests(TestCase):
    def setUp(self):
        self.libro = crear_libro()
        self.otro = crear_libro(titulo="Arquitectura Limpia", precio="250.00", cantidad=5)
        self.builder = OrdenBuilder()

    def test_sin_productos_lanza_datos_insuficientes(self):
        with self.assertRaisesMessage(ValueError, "Datos insuficientes"):
            self.builder.con_usuario(None).para_envio("Calle 123").build()
        self.assertEqual(Orden.objects.count(), 0)

    def test_el_total_incluye_el_iva_de_1_19(self):
        orden = self.builder.con_productos([self.libro, self.otro]).build()
        # (150 + 250) * 1.19 = 476
        self.assertEqual(orden.total, Decimal("476.00"))
        orden.refresh_from_db()
        self.assertEqual(orden.total, Decimal("476.00"))

    def test_un_solo_libro_150_da_178_50(self):
        orden = self.builder.con_productos([self.libro]).build()
        self.assertEqual(orden.total, Decimal("178.50"))

    def test_un_libro_repetido_cuenta_como_mas_unidades(self):
        orden = self.builder.con_productos([self.libro, self.libro]).build()
        self.assertEqual(orden.total, Decimal("357.00"))

    def test_guarda_usuario_direccion_y_libro_principal(self):
        usuario = get_user_model().objects.create_user("juan", password="x")
        orden = (
            self.builder
            .con_usuario(usuario)
            .con_productos([self.libro, self.otro])
            .para_envio("Calle 123 #45-67")
            .build()
        )
        orden.refresh_from_db()
        self.assertEqual(orden.usuario, usuario)
        self.assertEqual(orden.direccion_envio, "Calle 123 #45-67")
        self.assertEqual(orden.libro, self.libro)

    def test_el_usuario_es_opcional(self):
        orden = self.builder.con_productos([self.libro]).build()
        self.assertIsNone(orden.usuario)
        self.assertEqual(orden.direccion_envio, "")

    def test_interfaz_fluida_cada_paso_devuelve_el_builder(self):
        self.assertIs(self.builder.con_usuario(None), self.builder)
        self.assertIs(self.builder.con_productos([self.libro]), self.builder)
        self.assertIs(self.builder.para_envio("x"), self.builder)

    def test_despues_de_build_el_estado_se_reinicia(self):
        usuario = get_user_model().objects.create_user("ana", password="x")
        self.builder.con_usuario(usuario).con_productos([self.libro]).para_envio("Calle 1").build()

        # Sin volver a configurar nada, la segunda orden no puede salir
        with self.assertRaises(ValueError):
            self.builder.build()
        self.assertIsNone(self.builder._usuario)
        self.assertEqual(self.builder._direccion, "")
        self.assertEqual(self.builder._items, [])
        self.assertEqual(Orden.objects.count(), 1)

    def test_reset_limpia_a_mitad_de_la_construccion(self):
        self.builder.con_productos([self.libro]).para_envio("Calle 1")
        self.builder.reset()
        with self.assertRaises(ValueError):
            self.builder.build()
