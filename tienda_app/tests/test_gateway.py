import os

from django.test import SimpleTestCase, override_settings

from tienda_app.domain.interfaces import ProcesadorPago
from tienda_app.infra.gateways import ARCHIVO_LOG, BancoNacionalProcesador

from .base import LogTemporalMixin


class BancoNacionalProcesadorTests(LogTemporalMixin, SimpleTestCase):
    def test_implementa_la_interfaz_de_pago(self):
        self.assertIsInstance(BancoNacionalProcesador(), ProcesadorPago)

    def test_el_log_lleva_el_nombre_del_estudiante(self):
        self.assertEqual(ARCHIVO_LOG, "pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log")

    def test_cada_pago_agrega_una_linea_al_log(self):
        banco = BancoNacionalProcesador()
        for monto in (178.5, 297.5, 249.9):
            self.assertTrue(banco.pagar(monto))

        ruta = os.path.join(self.carpeta_log, ARCHIVO_LOG)
        with open(ruta, encoding="utf-8") as f:
            lineas = f.read().splitlines()
        self.assertEqual(len(lineas), 3)
        self.assertIn("Transaccion exitosa por : $178.5", lineas[0])

    def test_por_defecto_el_log_va_a_la_raiz_del_proyecto(self):
        from django.conf import settings

        with override_settings():
            del settings.PAGOS_LOG_DIR  # vuelve al valor por defecto del gateway
            ruta = BancoNacionalProcesador()._ruta_log()
        self.assertEqual(ruta.parent, settings.BASE_DIR)
