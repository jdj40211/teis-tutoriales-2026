from django.conf import settings
from django.db import models

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.titulo

    @property
    def stock_actual(self):
        """Unidades disponibles. LibroSerializer lo expone como campo de solo lectura."""
        try:
            return self.inventario.cantidad
        except Inventario.DoesNotExist:
            return 0  # el libro todavía no tiene registro de inventario

class Inventario(models.Model):
    libro = models.OneToOneField(Libro, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

class Orden(models.Model):
    # Tutorial 2: el OrdenBuilder también guarda quién compra y a dónde se envía.
    # El usuario es opcional porque las vistas y la API de la tienda no exigen login.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.CharField(max_length=200, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)