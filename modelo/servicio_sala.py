"""Servicio especializado: reserva de salas (cobro por hora)."""
from excepciones.errores import ErrorValidacion
from modelo.servicio import Servicio

RECARGO_SALA_GRANDE = 0.15  # salas de mas de 20 personas
CAPACIDAD_GRANDE = 20


class ServicioSala(Servicio):
    """Reserva de salas de reuniones o capacitacion."""

    prefijo = "SAL"
    unidad = "hora"
    duracion_minima = 1
    duracion_maxima = 12

    def __init__(self, nombre, costo_base, capacidad, ubicacion="Sede principal", disponible=True):
        super().__init__(nombre, costo_base, disponible)
        self.capacidad = capacidad
        self.ubicacion = ubicacion

    @property
    def capacidad(self):
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor):
        try:
            numero = int(valor)
        except (TypeError, ValueError) as exc:
            raise ErrorValidacion(f"Capacidad de sala no numerica: {valor!r}.") from exc
        if not 2 <= numero <= 100:
            raise ErrorValidacion(f"La capacidad debe estar entre 2 y 100 personas (recibido {numero}).")
        self._capacidad = numero

    @property
    def ubicacion(self):
        return self._ubicacion

    @ubicacion.setter
    def ubicacion(self, valor):
        texto = str(valor).strip() if valor else ""
        self._ubicacion = texto or "Sede principal"

    # ---------------- metodos sobrescritos (polimorfismo) ----------------
    def validar_parametros(self, duracion):
        horas = self._validar_duracion(duracion)
        if self._capacidad > CAPACIDAD_GRANDE and horas > 8:
            raise ErrorValidacion(
                "Las salas de mas de 20 personas solo se reservan hasta 8 horas continuas."
            )
        return horas

    def calcular_costo(self, duracion):
        horas = self.validar_parametros(duracion)
        costo = self.costo_base * horas
        if self._capacidad > CAPACIDAD_GRANDE:
            costo *= 1 + RECARGO_SALA_GRANDE
        return round(costo, 2)

    def describir(self):
        return (
            f"{super().describir()} | capacidad {self._capacidad} personas "
            f"| ubicacion {self._ubicacion}"
        )
