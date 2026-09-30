import io
import os
from contextlib import redirect_stdout
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .base import LogTemporalMixin, crear_libro


class InventarioHTMLTests(LogTemporalMixin, TestCase):
    """Las dos puertas (HTML y API) conducen a la misma habitación (la lógica de negocio)."""

    def setUp(self):
        super().setUp()
        self.libro = crear_libro(cantidad=10)
        patcher = mock.patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def stock_en_la_pagina(self):
        respuesta = self.client.get(reverse("inventario"))
        self.assertEqual(respuesta.status_code, 200)
        return respuesta, respuesta.context["libros"][0].stock_actual

    def test_la_pagina_lista_el_libro_con_su_stock(self):
        respuesta, stock = self.stock_en_la_pagina()
        self.assertEqual(stock, 10)
        self.assertContains(respuesta, "Clean Code en Python")
        self.assertContains(respuesta, f'data-libro-id="{self.libro.id}">10</td>')

    def test_la_raiz_tambien_muestra_el_inventario(self):
        self.assertTemplateUsed(self.client.get("/"), "tienda_app/inventario.html")

    def test_una_compra_por_la_api_se_refleja_en_la_vista_html(self):
        _, antes = self.stock_en_la_pagina()

        with redirect_stdout(io.StringIO()):
            respuesta_api = APIClient().post(
                reverse("api_comprar"),
                {"libro_id": self.libro.id, "direccion_envio": "Calle 123"},
                format="json",
            )
        self.assertEqual(respuesta_api.status_code, 201)

        respuesta, despues = self.stock_en_la_pagina()
        self.assertEqual((antes, despues), (10, 9))
        self.assertContains(respuesta, f'data-libro-id="{self.libro.id}">9</td>')

    def test_una_compra_por_la_vista_html_tambien_se_refleja_en_la_api(self):
        with redirect_stdout(io.StringIO()):
            self.client.post(reverse("compra_rapida", args=[self.libro.id]))
        productos = APIClient().get(reverse("api_productos")).json()
        self.assertEqual(productos[0]["stock_actual"], 9)

    def test_sin_libros_muestra_un_aviso(self):
        from tienda_app.models import Libro

        Libro.objects.all().delete()
        self.assertContains(self.client.get(reverse("inventario")), "preparar_datos")
