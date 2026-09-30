from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from tienda_app.models import Inventario, Libro, Orden


class PrepararDatosTests(TestCase):
    def ejecutar(self, *args):
        salida = StringIO()
        call_command("preparar_datos", *args, stdout=salida)
        return salida.getvalue()

    def test_crea_los_libros_con_stock(self):
        self.ejecutar()
        self.assertEqual(Libro.objects.count(), 4)
        clean = Libro.objects.get(titulo="Clean Code en Python")
        self.assertEqual(float(clean.precio), 150.0)
        self.assertEqual(Inventario.objects.get(libro=clean).cantidad, 10)
        self.assertTrue(all(i.cantidad > 0 for i in Inventario.objects.all()))

    def test_se_puede_repetir_sin_duplicar_ni_pisar_stock(self):
        self.ejecutar()
        Inventario.objects.filter(libro__titulo="Clean Code en Python").update(cantidad=3)
        self.ejecutar()
        self.assertEqual(Libro.objects.count(), 4)
        self.assertEqual(Inventario.objects.get(libro__titulo="Clean Code en Python").cantidad, 3)

    def test_reiniciar_restaura_stock_y_borra_ordenes(self):
        self.ejecutar()
        clean = Libro.objects.get(titulo="Clean Code en Python")
        Inventario.objects.filter(libro=clean).update(cantidad=1)
        Orden.objects.create(libro=clean, total=178.5)

        self.ejecutar("reiniciar")

        self.assertEqual(Inventario.objects.get(libro=clean).cantidad, 10)
        self.assertEqual(Orden.objects.count(), 0)
