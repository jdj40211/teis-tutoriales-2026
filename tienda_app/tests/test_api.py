import io
import os
from contextlib import redirect_stdout
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tienda_app.infra.gateways import ARCHIVO_LOG
from tienda_app.models import Inventario, Orden

from .base import LogTemporalMixin, ProcesadorFalso, crear_libro


class CompraAPITests(LogTemporalMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.cliente = APIClient()
        self.url = reverse("api_comprar")
        self.libro = crear_libro(cantidad=2)
        # Por defecto las pruebas usan el Mock, como en el Tutorial 2
        patcher = mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def stock(self):
        return Inventario.objects.get(libro=self.libro).cantidad

    def comprar(self, payload):
        with redirect_stdout(io.StringIO()):
            return self.cliente.post(self.url, payload, format="json")

    def test_la_ruta_es_api_v1_comprar(self):
        self.assertEqual(self.url, "/api/v1/comprar/")

    def test_compra_exitosa_responde_201_con_el_cuerpo_del_enunciado(self):
        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 123"})

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json(), {"estado": "exito", "mensaje": "Orden creada. Total: 178.50"})

    def test_la_compra_descuenta_inventario_y_crea_la_orden(self):
        self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 123"})

        self.assertEqual(self.stock(), 1)
        orden = Orden.objects.get()
        self.assertEqual(orden.libro, self.libro)
        self.assertEqual(orden.total, Decimal("178.50"))
        self.assertEqual(orden.direccion_envio, "Calle 123")
        self.assertIsNone(orden.usuario)  # sin login la compra queda sin usuario

    def test_con_sesion_iniciada_la_orden_guarda_el_usuario(self):
        usuario = get_user_model().objects.create_user("juan", password="x")
        self.cliente.force_login(usuario)

        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 123"})

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Orden.objects.get().usuario, usuario)

    def test_cantidad_opcional_compra_varias_unidades(self):
        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 1", "cantidad": 2})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["mensaje"], "Orden creada. Total: 357.00")
        self.assertEqual(self.stock(), 0)

    def test_payload_invalido_responde_400_con_los_errores(self):
        casos = [
            ({}, {"libro_id", "direccion_envio"}),
            ({"libro_id": self.libro.id}, {"direccion_envio"}),
            ({"libro_id": "abc", "direccion_envio": "Calle 1"}, {"libro_id"}),
            ({"libro_id": self.libro.id, "direccion_envio": ""}, {"direccion_envio"}),
            ({"libro_id": self.libro.id, "direccion_envio": "x" * 201}, {"direccion_envio"}),
            ({"libro_id": self.libro.id, "direccion_envio": "Calle 1", "cantidad": 0}, {"cantidad"}),
            ({"libro_id": self.libro.id, "direccion_envio": "Calle 1", "cantidad": 101}, {"cantidad"}),
            ({"libro_id": 0, "direccion_envio": "Calle 1"}, {"libro_id"}),
            ({"libro_id": 10**30, "direccion_envio": "Calle 1"}, {"libro_id"}),
        ]
        for payload, campos_con_error in casos:
            with self.subTest(payload=payload):
                respuesta = self.comprar(payload)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(set(respuesta.json()), campos_con_error)

        self.assertEqual(self.stock(), 2)
        self.assertEqual(Orden.objects.count(), 0)

    def test_sin_stock_responde_409_y_no_cambia_nada(self):
        Inventario.objects.filter(libro=self.libro).update(cantidad=0)

        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 1"})

        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("stock", respuesta.json()["error"])
        self.assertEqual(self.stock(), 0)
        self.assertEqual(Orden.objects.count(), 0)

    def test_pedir_mas_unidades_que_el_stock_responde_409(self):
        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 1", "cantidad": 3})
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(self.stock(), 2)

    def test_libro_sin_registro_de_inventario_responde_409(self):
        Inventario.objects.filter(libro=self.libro).delete()
        respuesta = self.comprar({"libro_id": self.libro.id, "direccion_envio": "Calle 1"})
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Orden.objects.count(), 0)

    def test_libro_inexistente_responde_404(self):
        respuesta = self.comprar({"libro_id": 9999, "direccion_envio": "Calle 1"})
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json(), {"error": "El libro no existe."})

    def test_pago_rechazado_responde_500_sin_descontar(self):
        with mock.patch("tienda_app.api.views.PaymentFactory.get_processor", return_value=ProcesadorFalso(False)):
            with self.assertLogs("tienda_app.api.views", level="ERROR"):
                respuesta = self.cliente.post(
                    self.url, {"libro_id": self.libro.id, "direccion_envio": "Calle 1"}, format="json"
                )
        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json(), {"error": "Error interno"})
        self.assertEqual(self.stock(), 2)
        self.assertEqual(Orden.objects.count(), 0)

    def test_solo_acepta_post(self):
        self.assertEqual(self.cliente.get(self.url).status_code, 405)

    def test_la_interfaz_web_de_drf_muestra_el_formulario_para_enviar_el_post(self):
        respuesta = self.cliente.get(self.url, HTTP_ACCEPT="text/html")
        self.assertEqual(respuesta.status_code, 405)
        self.assertContains(respuesta, "post-generic-content-form", status_code=405)

    def test_con_el_banco_real_se_escribe_el_log_del_estudiante(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("PAYMENT_PROVIDER", None)
            respuesta = self.cliente.post(
                self.url, {"libro_id": self.libro.id, "direccion_envio": "Calle 1"}, format="json"
            )
        self.assertEqual(respuesta.status_code, 201)
        with open(os.path.join(self.carpeta_log, ARCHIVO_LOG), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1)


class ProductosAPITests(TestCase):
    def test_lista_los_libros_con_su_stock(self):
        crear_libro(titulo="Clean Code en Python", precio="150.00", cantidad=10)
        crear_libro(titulo="Arquitectura Limpia", precio="250.00", cantidad=5)

        respuesta = APIClient().get(reverse("api_productos"))

        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual([d["titulo"] for d in datos], ["Clean Code en Python", "Arquitectura Limpia"])
        self.assertEqual(set(datos[0]), {"id", "titulo", "precio", "stock_actual"})
        self.assertEqual(datos[0]["precio"], "150.00")
        self.assertEqual([d["stock_actual"] for d in datos], [10, 5])

    def test_ruta_y_lista_vacia(self):
        self.assertEqual(reverse("api_productos"), "/api/v1/productos/")
        self.assertEqual(APIClient().get("/api/v1/productos/").json(), [])

    def test_un_libro_sin_inventario_muestra_stock_cero(self):
        from tienda_app.models import Libro

        Libro.objects.create(titulo="Sin registro", precio=Decimal("10.00"))
        self.assertEqual(APIClient().get("/api/v1/productos/").json()[0]["stock_actual"], 0)
