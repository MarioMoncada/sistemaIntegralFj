"""
Excepciones personalizadas del sistema Software FJ.

Todas heredan de ErrorSistemaFJ, lo que permite capturar de forma
general cualquier error controlado del dominio con un solo except.
"""


class ErrorSistemaFJ(Exception):
    """Excepcion base de la aplicacion."""

    def __init__(self, mensaje="Error no especificado del sistema FJ"):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ErrorValidacion(ErrorSistemaFJ):
    """Datos invalidos o parametros faltantes."""


class ErrorRegistroDuplicado(ErrorSistemaFJ):
    """Se intenta registrar una entidad que ya existe."""


class ErrorNoEncontrado(ErrorSistemaFJ):
    """No existe la entidad solicitada en las listas internas."""


class ErrorServicioNoDisponible(ErrorSistemaFJ):
    """El servicio existe pero esta marcado como no disponible."""


class ErrorReservaInvalida(ErrorSistemaFJ):
    """La reserva no puede crearse con los datos entregados."""


class ErrorOperacionNoPermitida(ErrorSistemaFJ):
    """La operacion no es valida para el estado actual del objeto."""


class ErrorCalculoCosto(ErrorSistemaFJ):
    """Inconsistencia durante el calculo de costos."""
