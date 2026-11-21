"""Servicio especializado: alquiler de equipos (cobro por dia y unidad)."""
from excepciones.errores import ErrorValidacion
from modelo.servicio import Servicio

PORCENTAJE_DEPOSITO = 0.10  # deposito de garantia sobre el alquiler


class ServicioEquipo(Servicio):
    """Alquiler de equipos de computo o audiovisuales."""

    prefijo = "EQU"
    unidad = "dia"
    duracion_minima = 1
    duracion_maxima = 30

    def __init__(self, nombre, costo_base, cantidad, tipo_equipo="computo", disponible=True):
        super().__init__(nombre, costo_base, disponible)
        self.cantidad = cantidad
        self.tipo_equipo = tipo_equipo

    @property
    def cantidad(self):
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor):
        try:
            numero = int(valor)
        except (TypeError, ValueError) as exc:
            raise ErrorValidacion(f"Cantidad de equipos no numerica: {valor!r}.") from exc
        if not 1 <= numero <= 50:
            raise ErrorValidacion(f"La cantidad de equipos debe estar entre 1 y 50 (recibido {numero}).")
        self._cantidad = numero

    @property
    def tipo_equipo(self):
        return self._tipo_equipo

    @tipo_equipo.setter
    def tipo_equipo(self, valor):
        texto = str(valor).strip().lower() if valor else ""
        self._tipo_equipo = texto or "computo"

    # ---------------- metodos sobrescritos (polimorfismo) ----------------
    def validar_parametros(self, duracion):
        dias = self._validar_duracion(duracion)
        if self._cantidad > 20 and dias > 15:
            raise ErrorValidacion(
                "Los alquileres de mas de 20 equipos no superan los 15 dias."
            )
        return dias

    def calcular_costo(self, duracion):
        dias = self.validar_parametros(duracion)
        alquiler = self.costo_base * self._cantidad * dias
        deposito = alquiler * PORCENTAJE_DEPOSITO
        return round(alquiler + deposito, 2)

    def describir(self):
        return (
            f"{super().describir()} | {self._cantidad} equipo(s) de {self._tipo_equipo} "
            f"| incluye deposito del {PORCENTAJE_DEPOSITO:.0%}"
        )
