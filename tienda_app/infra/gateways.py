import datetime
from pathlib import Path

from django.conf import settings

from ..domain.interfaces import ProcesadorPago

# Tutorial 1, Paso 4: el nombre del archivo lleva mi identidad para que la
# evidencia de ejecución sea única.
ARCHIVO_LOG = "pagos_locales_JUAN_DAVID_SIERRA_OROZCO.log"


class BancoNacionalProcesador(ProcesadorPago):
    """
    Implementación concreta de la infraestructura.
    Simula un banco local escribiendo cada transacción en un archivo de log.
    """

    def _ruta_log(self) -> Path:
        # El log queda en la raíz del proyecto sin importar desde qué carpeta
        # se lance el servidor. En las pruebas PAGOS_LOG_DIR apunta a una
        # carpeta temporal para no ensuciar el proyecto.
        carpeta = Path(getattr(settings, "PAGOS_LOG_DIR", settings.BASE_DIR))
        return carpeta / ARCHIVO_LOG

    def pagar(self, monto: float) -> bool:
        # Simulamos una operación de red o persistencia externa
        with open(self._ruta_log(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] Transaccion exitosa por : ${monto}\n")
        return True
