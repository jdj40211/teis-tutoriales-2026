from rest_framework import serializers

from tienda_app.models import Libro


class LibroSerializer(serializers.ModelSerializer):
    # stock_actual es una propiedad del modelo Libro (campo calculado, solo lectura)
    class Meta:
        model = Libro
        fields = ['id', 'titulo', 'precio', 'stock_actual']


class OrdenInputSerializer(serializers.Serializer):
    """
    Serializer para VALIDAR la entrada de datos, no ligado a un modelo.
    Actúa como un DTO (Data Transfer Object). Solo valida la forma del JSON;
    las reglas de negocio (stock, pago) las decide el servicio.
    """
    libro_id = serializers.IntegerField(min_value=1, max_value=2147483647)
    direccion_envio = serializers.CharField(max_length=200)
    # Extra sobre el PDF: unidades a comprar (por defecto 1, como en el payload del enunciado).
    # El tope evita pedidos absurdos que el servicio tendría que armar en memoria.
    cantidad = serializers.IntegerField(min_value=1, max_value=100, default=1)
