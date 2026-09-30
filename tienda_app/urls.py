from django.urls import path
from .views import CompraRapidaView, CompraView

urlpatterns = [
    # Usamos .as_view() para habilitar la CBV
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
    path('compra-rapida/<int:libro_id>/', CompraRapidaView.as_view(), name='compra_rapida'),
]