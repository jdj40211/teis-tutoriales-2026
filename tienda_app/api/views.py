import logging

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda_app.infra.factories import PaymentFactory
from tienda_app.services import CompraService, InventarioService

from .serializers import LibroSerializer, OrdenInputSerializer

logger = logging.getLogger(__name__)


class CompraAPIView(APIView):
    """
    Endpoint para procesar compras via JSON.
    POST /api/v1/comprar/
    Payload: {"libro_id": 1, "direccion_envio": "Calle 123", "cantidad": 1}
    (cantidad es opcional y vale 1 por defecto)
    """

    def post(self, request):
        # 1. Validación de datos de entrada (Adapter)
        serializer = OrdenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data

        try:
            # 2. Inyección de Dependencias (Factory)
            gateway = PaymentFactory.get_processor()

            # 3. Ejecución de lógica de negocio (Service Layer)
            servicio = CompraService(procesador_pago=gateway)

            # Notese que el servicio NO cambia, solo cambia quien lo llama.
            # Sin sesión iniciada request.user es AnonymousUser, que no se puede
            # guardar en la clave foránea de Orden; en ese caso la compra va sin usuario.
            usuario = request.user if request.user.is_authenticated else None
            resultado = servicio.ejecutar_compra(
                libro_id=datos['libro_id'],
                cantidad=datos['cantidad'],
                direccion=datos['direccion_envio'],
                usuario=usuario,
            )

            return Response(
                {
                    'estado': 'exito',
                    'mensaje': f'Orden creada. Total: {resultado}',
                },
                status=status.HTTP_201_CREATED,
            )

        except Http404:
            # El servicio usa get_object_or_404: el libro no existe
            return Response({'error': 'El libro no existe.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            # Errores de negocio (ej: sin stock)
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            # Errores inesperados (ej: el banco rechazó el pago)
            logger.exception('Error inesperado al procesar la compra por la API')
            return Response({'error': 'Error interno'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductoListAPIView(APIView):
    """
    GET /api/v1/productos/
    Lista los libros en JSON con su stock actual. Reutiliza el mismo servicio de
    inventario que la página HTML /inventario/.
    """

    def get(self, request):
        libros = InventarioService().listar_libros()
        return Response(LibroSerializer(libros, many=True).data)
