from django.urls import path

from .api.views import CompraAPIView, ProductoListAPIView
from .views import CompraRapidaView, CompraView, InventarioView

urlpatterns = [
    # Página de inicio: el inventario (a ella apunta "Volver a la tienda")
    path('', InventarioView.as_view(), name='inicio'),
    path('inventario/', InventarioView.as_view(), name='inventario'),
    # Usamos .as_view() para habilitar la CBV
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
    path('compra-rapida/<int:libro_id>/', CompraRapidaView.as_view(), name='compra_rapida'),
    # API REST (Tutorial 3)
    path('api/v1/comprar/', CompraAPIView.as_view(), name='api_comprar'),
    path('api/v1/productos/', ProductoListAPIView.as_view(), name='api_productos'),
]
