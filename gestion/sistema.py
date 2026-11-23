"""
Clase SistemaFJ: gestor central de la aplicacion.

Mantiene las listas internas de clientes, servicios y reservas
(sin base de datos) y registra en la bitacora cada evento y error.
"""
from excepciones.errores import (
    ErrorNoEncontrado,
    ErrorRegistroDuplicado,
    ErrorSistemaFJ,
    ErrorValidacion,
)
from modelo.cliente import Cliente
from modelo.reserva import Reserva
from modelo.servicio_asesoria import ServicioAsesoria
from modelo.servicio_equipo import ServicioEquipo
from modelo.servicio_sala import ServicioSala
from utilidades.registro import registrar_error, registrar_evento

# Fabrica de servicios: tipo -> (clase, nombres de los parametros extra)
TIPOS_SERVICIO = {
    "sala": (ServicioSala, ("capacidad", "ubicacion")),
    "equipo": (ServicioEquipo, ("cantidad", "tipo_equipo")),
    "asesoria": (ServicioAsesoria, ("especialidad", "nivel")),
}


class SistemaFJ:
    """Fachada de gestion para clientes, servicios y reservas."""

    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []

    # ---- acceso de solo lectura a las listas internas (encapsulacion) ----
    @property
    def clientes(self):
        return tuple(self._clientes)

    @property
    def servicios(self):
        return tuple(self._servicios)

    @property
    def reservas(self):
        return tuple(self._reservas)

    # --------------------------- clientes ---------------------------
    def registrar_cliente(self, nombre, documento, email, telefono, categoria="regular"):
        """Crea y almacena un cliente. Lanza ErrorSistemaFJ si los datos no son validos."""
        try:
            cliente = Cliente(nombre, documento, email, telefono, categoria)
            if any(c.documento == cliente.documento for c in self._clientes):
                raise ErrorRegistroDuplicado(
                    f"Ya existe un cliente con el documento {cliente.documento}."
                )
        except ErrorSistemaFJ as exc:
            registrar_error(f"Registro de cliente rechazado ({nombre!r})", exc)
            raise
        else:
            self._clientes.append(cliente)
            registrar_evento(f"Cliente registrado: {cliente.resumen()}")
            return cliente
        finally:
            registrar_evento(f"Clientes en memoria: {len(self._clientes)}")

    def buscar_cliente(self, identificador):
        texto = str(identificador).strip().upper()
        for cliente in self._clientes:
            if cliente.identificador == texto or cliente.documento == texto:
                return cliente
        error = ErrorNoEncontrado(f"No existe el cliente {identificador!r}.")
        registrar_error("Busqueda de cliente fallida", error)
        raise error

    # --------------------------- servicios ---------------------------
    def registrar_servicio(self, tipo, nombre, costo_base, extra1=None, extra2=None):
        """
        Crea un servicio especializado segun el tipo ('sala', 'equipo', 'asesoria').
        extra1 y extra2 son los parametros propios de cada especializacion.
        """
        clave = str(tipo).strip().lower()
        try:
            if clave not in TIPOS_SERVICIO:
                raise ErrorValidacion(
                    f"Tipo de servicio {tipo!r} no soportado. "
                    f"Opciones: {', '.join(TIPOS_SERVICIO)}."
                )
            clase, parametros = TIPOS_SERVICIO[clave]
            argumentos = {}
            for nombre_parametro, valor in zip(parametros, (extra1, extra2)):
                if valor not in (None, ""):
                    argumentos[nombre_parametro] = valor
            if parametros[0] not in argumentos:
                raise ErrorValidacion(
                    f"Parametro faltante '{parametros[0]}' para el servicio de tipo {clave}."
                )
            servicio = clase(nombre, costo_base, **argumentos)
        except ErrorSistemaFJ as exc:
            registrar_error(f"Creacion de servicio rechazada ({nombre!r}, tipo {tipo!r})", exc)
            raise
        except TypeError as exc:
            error = ErrorValidacion(f"Parametros incorrectos para el servicio {nombre!r}.")
            registrar_error("Creacion de servicio rechazada", error)
            raise error from exc
        else:
            self._servicios.append(servicio)
            registrar_evento(f"Servicio creado: {servicio.resumen()}")
            return servicio

    def buscar_servicio(self, identificador):
        texto = str(identificador).strip().upper()
        for servicio in self._servicios:
            if servicio.identificador == texto:
                return servicio
        error = ErrorNoEncontrado(f"No existe el servicio {identificador!r}.")
        registrar_error("Busqueda de servicio fallida", error)
        raise error

    def alternar_disponibilidad(self, identificador):
        servicio = self.buscar_servicio(identificador)
        nuevo = servicio.cambiar_disponibilidad(not servicio.disponible)
        registrar_evento(
            f"Servicio {servicio.identificador} ahora esta "
            f"{'disponible' if nuevo else 'no disponible'}"
        )
        return nuevo

    # --------------------------- reservas ---------------------------
    def crear_reserva(self, id_cliente, id_servicio, duracion, aplicar_descuento=True):
        try:
            cliente = self.buscar_cliente(id_cliente)
            servicio = self.buscar_servicio(id_servicio)
            reserva = Reserva(cliente, servicio, duracion, aplicar_descuento)
        except ErrorSistemaFJ as exc:
            registrar_error(
                f"Reserva rechazada (cliente {id_cliente!r}, servicio {id_servicio!r})", exc
            )
            raise
        else:
            self._reservas.append(reserva)
            registrar_evento(f"Reserva creada: {reserva.resumen()}")
            return reserva

    def buscar_reserva(self, identificador):
        texto = str(identificador).strip().upper()
        for reserva in self._reservas:
            if reserva.identificador == texto:
                return reserva
        error = ErrorNoEncontrado(f"No existe la reserva {identificador!r}.")
        registrar_error("Busqueda de reserva fallida", error)
        raise error

    def confirmar_reserva(self, identificador):
        reserva = self.buscar_reserva(identificador)
        try:
            return reserva.confirmar()
        except ErrorSistemaFJ as exc:
            registrar_error(f"Confirmacion rechazada ({identificador})", exc)
            raise

    def procesar_reserva(self, identificador):
        reserva = self.buscar_reserva(identificador)
        try:
            return reserva.procesar()
        except ErrorSistemaFJ as exc:
            registrar_error(f"Procesamiento rechazado ({identificador})", exc)
            raise

    def cancelar_reserva(self, identificador, motivo="Solicitud del cliente"):
        reserva = self.buscar_reserva(identificador)
        try:
            return reserva.cancelar(motivo)
        except ErrorSistemaFJ as exc:
            registrar_error(f"Cancelacion rechazada ({identificador})", exc)
            raise

    # --------------------------- consultas ---------------------------
    def estadisticas(self):
        """Resumen general; demuestra polimorfismo al recorrer servicios distintos."""
        procesadas = [r for r in self._reservas if r.estado == "PROCESADA"]
        return {
            "clientes": len(self._clientes),
            "servicios": len(self._servicios),
            "reservas": len(self._reservas),
            "procesadas": len(procesadas),
            "canceladas": len([r for r in self._reservas if r.estado == "CANCELADA"]),
            "facturado": round(sum(r.costo_total for r in procesadas), 2),
        }

    def catalogo(self):
        """Lista de descripciones polimorficas de todos los servicios."""
        return [servicio.resumen() for servicio in self._servicios]
