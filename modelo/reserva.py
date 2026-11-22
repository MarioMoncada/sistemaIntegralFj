"""
Clase Reserva: integra cliente, servicio, duracion y estado.

Implementa confirmacion, cancelacion y procesamiento usando
try/except, try/except/else/finally y encadenamiento de excepciones.
"""
from datetime import datetime

from excepciones.errores import (
    ErrorCalculoCosto,
    ErrorOperacionNoPermitida,
    ErrorReservaInvalida,
    ErrorSistemaFJ,
)
from modelo.cliente import Cliente
from modelo.entidad import EntidadBase
from modelo.servicio import Servicio
from utilidades.registro import registrar_error, registrar_evento

PENDIENTE = "PENDIENTE"
CONFIRMADA = "CONFIRMADA"
PROCESADA = "PROCESADA"
CANCELADA = "CANCELADA"
ESTADOS = (PENDIENTE, CONFIRMADA, PROCESADA, CANCELADA)


class Reserva(EntidadBase):
    """Reserva de un servicio por parte de un cliente."""

    prefijo = "RES"

    def __init__(self, cliente, servicio, duracion, aplicar_descuento_cliente=True):
        super().__init__()
        if not isinstance(cliente, Cliente):
            raise ErrorReservaInvalida("La reserva requiere un objeto Cliente valido.")
        if not isinstance(servicio, Servicio):
            raise ErrorReservaInvalida("La reserva requiere un objeto Servicio valido.")

        self._cliente = cliente
        self._servicio = servicio
        self._aplicar_descuento_cliente = bool(aplicar_descuento_cliente)
        self._estado = PENDIENTE
        self._costo_total = 0.0
        self._observaciones = []
        self._duracion = self._validar_duracion(duracion)
        self.validar()

    # ------------------- propiedades encapsuladas -------------------
    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    @property
    def observaciones(self):
        return tuple(self._observaciones)

    # ------------------------- validaciones -------------------------
    def _validar_duracion(self, duracion):
        try:
            valor = int(duracion)
        except (TypeError, ValueError) as exc:
            raise ErrorReservaInvalida(f"Duracion de reserva invalida: {duracion!r}.") from exc
        if valor <= 0:
            raise ErrorReservaInvalida("La duracion de la reserva debe ser mayor que cero.")
        return valor

    def validar(self):
        """Comprueba que el servicio acepte la reserva tal como fue solicitada."""
        try:
            self._servicio.verificar_disponibilidad()
            self._servicio.validar_parametros(self._duracion)
        except ErrorSistemaFJ as exc:
            # encadenamiento: la causa original queda disponible en __cause__
            raise ErrorReservaInvalida(
                f"No se puede reservar {self._servicio.nombre} para {self._cliente.nombre}."
            ) from exc
        return True

    def _exigir_estado(self, *estados_permitidos):
        if self._estado not in estados_permitidos:
            raise ErrorOperacionNoPermitida(
                f"Operacion no permitida: la reserva {self._identificador} esta "
                f"{self._estado} y se requiere {' o '.join(estados_permitidos)}."
            )

    # ------------------------ ciclo de vida ------------------------
    def confirmar(self):
        """Pasa la reserva de PENDIENTE a CONFIRMADA."""
        self._exigir_estado(PENDIENTE)
        try:
            self.validar()
        except ErrorSistemaFJ as exc:
            registrar_error(f"Fallo al confirmar {self._identificador}", exc)
            raise
        else:
            self._estado = CONFIRMADA
            self._anotar("Reserva confirmada")
            registrar_evento(f"Reserva {self._identificador} confirmada")
            return self._estado

    def cancelar(self, motivo="Sin motivo registrado"):
        """Cancela una reserva pendiente o confirmada."""
        if self._estado == PROCESADA:
            raise ErrorOperacionNoPermitida(
                f"La reserva {self._identificador} ya fue procesada y no puede cancelarse."
            )
        self._exigir_estado(PENDIENTE, CONFIRMADA)
        self._estado = CANCELADA
        self._anotar(f"Cancelada: {motivo}")
        registrar_evento(f"Reserva {self._identificador} cancelada ({motivo})")
        return self._estado

    def procesar(self):
        """
        Liquida la reserva confirmada calculando su costo final.
        Usa try/except/else/finally.
        """
        self._exigir_estado(CONFIRMADA)
        descuento = (
            self._cliente.descuento_por_categoria() if self._aplicar_descuento_cliente else 0.0
        )
        try:
            total = self._servicio.calcular_total(self._duracion, descuento=descuento)
        except ErrorSistemaFJ as exc:
            registrar_error(f"Fallo procesando la reserva {self._identificador}", exc)
            self._anotar(f"Error al procesar: {exc.mensaje}")
            raise
        except Exception as exc:
            raise ErrorCalculoCosto(
                f"Error inesperado al liquidar la reserva {self._identificador}."
            ) from exc
        else:
            self._costo_total = total
            self._estado = PROCESADA
            self._anotar(f"Procesada por ${total:,.2f}")
            self._cliente.registrar_en_historial(
                f"{self._identificador} - {self._servicio.nombre} - ${total:,.2f}"
            )
            registrar_evento(
                f"Reserva {self._identificador} procesada | cliente {self._cliente.identificador} "
                f"| servicio {self._servicio.identificador} | total ${total:,.2f}"
            )
            return total
        finally:
            # se ejecuta siempre: haya exito o error
            registrar_evento(
                f"Fin del intento de procesamiento de {self._identificador} (estado {self._estado})"
            )

    def cotizacion(self):
        """Desglose del cobro sin cambiar el estado de la reserva."""
        descuento = (
            self._cliente.descuento_por_categoria() if self._aplicar_descuento_cliente else 0.0
        )
        return self._servicio.desglose(self._duracion, descuento=descuento)

    # --------------------------- utilidades ---------------------------
    def _anotar(self, texto):
        self._observaciones.append(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {texto}")

    def describir(self):
        return (
            f"Reserva de {self._cliente.nombre} | {self._servicio.nombre} "
            f"| {self._duracion} {self._servicio.unidad}(s) | estado {self._estado} "
            f"| total ${self._costo_total:,.2f}"
        )
