from decimal import Decimal

from django.test import SimpleTestCase

from tienda_app.domain.logic import CalculadorImpuestos


class CalculadorImpuestosTests(SimpleTestCase):
    def total(self, precio):
        return CalculadorImpuestos.obtener_total_con_iva(precio)

    def test_aplica_el_iva_de_1_19(self):
        self.assertEqual(self.total(Decimal("150.00")), Decimal("178.50"))
        self.assertEqual(self.total(Decimal("250.00")), Decimal("297.50"))

    def test_no_arrastra_ruido_de_float(self):
        # 210 * 1.19 en float da 249.89999999999998
        self.assertEqual(self.total(Decimal("210.00")), Decimal("249.90"))

    def test_redondea_los_centavos_hacia_arriba_en_la_mitad(self):
        self.assertEqual(self.total(Decimal("1.50")), Decimal("1.79"))  # 1.785
        self.assertEqual(self.total(Decimal("2.50")), Decimal("2.98"))  # 2.975

    def test_acepta_float_y_texto_y_devuelve_decimal(self):
        self.assertEqual(self.total(150.0), Decimal("178.50"))
        self.assertEqual(self.total("150"), Decimal("178.50"))
        self.assertIsInstance(self.total(10), Decimal)
