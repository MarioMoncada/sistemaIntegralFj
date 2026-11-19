"""
Bitacora (log) del sistema.

Centraliza el registro de eventos y errores en logs/sistema_fj.log.
Nunca lanza excepciones hacia la aplicacion: si el archivo no puede
escribirse, el programa sigue funcionando.
"""
import logging
import os
from datetime import datetime

CARPETA_LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
RUTA_LOG = os.path.join(CARPETA_LOGS, "sistema_fj.log")

_logger = None


def _obtener_logger():
    """Construye (una sola vez) el logger de la aplicacion."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        try:
            os.makedirs(CARPETA_LOGS, exist_ok=True)
            manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
        except OSError:
            manejador = logging.StreamHandler()
        manejador.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(manejador)

    _logger = logger
    return _logger


def registrar_evento(mensaje):
    """Registra una operacion exitosa o informativa."""
    _obtener_logger().info(mensaje)


def registrar_advertencia(mensaje):
    """Registra una situacion anomala que no detiene el sistema."""
    _obtener_logger().warning(mensaje)


def registrar_error(mensaje, excepcion=None):
    """
    Registra un error. Si la excepcion viene encadenada (raise ... from ...)
    tambien se deja constancia de la causa original.
    """
    texto = mensaje
    if excepcion is not None:
        texto = f"{mensaje} -> {type(excepcion).__name__}: {excepcion}"
        causa = excepcion.__cause__
        if causa is not None:
            texto += f" | causa original: {type(causa).__name__}: {causa}"
    _obtener_logger().error(texto)


def leer_bitacora(ultimas_lineas=200):
    """Devuelve el contenido del archivo de log para mostrarlo en la interfaz."""
    try:
        with open(RUTA_LOG, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        return "La bitacora aun no tiene registros."
    except OSError as exc:
        return f"No fue posible leer la bitacora: {exc}"
    return "".join(lineas[-ultimas_lineas:])


def iniciar_sesion_log():
    """Marca en el log el arranque de la aplicacion."""
    registrar_evento("=" * 60)
    registrar_evento(f"Inicio de sesion del sistema Software FJ ({datetime.now():%Y-%m-%d %H:%M:%S})")
