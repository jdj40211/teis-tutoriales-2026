from django.http import Http404
from django.views import View
from django.shortcuts import render, HttpResponse
from .services import CompraRapidaService, CompraService
from .infra.factories import PaymentFactory

class CompraView(View):
    """
    CBV: Vista Basada en Clases. 
    Actúa como un "Portero": recibe la petición y delega al servicio.
    """
    template_name = 'tienda_app/compra.html'
    
    # Configuramos el servicio con la infraestructura que entrega la fábrica
    def setup_service(self):
        # ANTES: gateway = BancoNacionalProcesador()
        # AHORA: delegación total a la Fábrica
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.ejecutar_compra(libro_id, cantidad=1)
            return render(request, self.template_name, {
                'mensaje_exito': f"¡Gracias por su compra! Total: ${total}",
                'total': total
            })
        except Http404:
            raise  # un libro que no existe debe responder 404, no 400
        except (ValueError, Exception) as e:
            # Manejo de errores de negocio transformados a respuesta de usuario
            return render(request, self.template_name, {
                'error': str(e)
            }, status=400)


class CompraRapidaView(View):
    """
    Tutorial 1: la vista queda como un puente entre la web y el servicio.
    Cada método tiene menos de 10 líneas y ninguna regla de negocio.
    """

    template_name = 'tienda_app/compra_rapida.html'

    def setup_service(self):
        return CompraRapidaService(procesador_pago=PaymentFactory.get_processor())

    def get(self, request, libro_id):
        contexto = self.setup_service().obtener_detalle(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.procesar(libro_id)
        except ValueError as error:
            return render(request, self.template_name, {'error': str(error)}, status=400)
        if total is None:
            return render(request, self.template_name, {'error': 'El banco rechazó el pago.'}, status=402)
        return render(request, self.template_name, {'mensaje_exito': f'Compra exitosa. Total: ${total}'})
