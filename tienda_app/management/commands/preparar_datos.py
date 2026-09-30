from django.core.management import call_command
from django.core.management.base import BaseCommand

from tienda_app.models import Inventario, Libro, Orden

# Libro de los enunciados (Clean Code en Python, 150.0, 10 unidades) más tres
# libros extra para poder hacer "tres compras de diferentes libros".
LIBROS_DE_PRUEBA = [
    ("Clean Code en Python", "150.00", 10),
    ("Arquitectura Limpia", "250.00", 5),
    ("Patrones de Diseño en Python", "180.00", 8),
    ("Django para Profesionales", "210.00", 6),
]


class Command(BaseCommand):
    help = (
        "Aplica las migraciones y crea los libros de prueba con su stock. "
        "Se puede repetir sin duplicar datos. Con el argumento 'reiniciar' "
        "deja el stock inicial y borra las órdenes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "modo",
            nargs="?",
            choices=["reiniciar"],
            help="Escriba 'reiniciar' para restaurar el stock y borrar las órdenes.",
        )

    def handle(self, *args, **options):
        call_command("migrate", interactive=False, verbosity=0)

        reiniciar = options["modo"] == "reiniciar"
        if reiniciar:
            Orden.objects.all().delete()

        for titulo, precio, cantidad in LIBROS_DE_PRUEBA:
            libro, creado = Libro.objects.get_or_create(titulo=titulo, defaults={"precio": precio})
            inventario, inv_creado = Inventario.objects.get_or_create(
                libro=libro, defaults={"cantidad": cantidad}
            )
            if reiniciar and not inv_creado:
                inventario.cantidad = cantidad
                inventario.save()
            estado = "creado" if creado else "ya existía"
            self.stdout.write(f"  [{libro.id}] {libro.titulo}: {inventario.cantidad} unidades ({estado})")

        self.stdout.write(self.style.SUCCESS("Datos de prueba listos."))
