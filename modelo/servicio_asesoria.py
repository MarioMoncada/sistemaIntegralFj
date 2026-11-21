"""Servicio especializado: asesorias especializadas (cobro por hora y nivel)."""
from excepciones.errores import ErrorValidacion
from modelo.servicio import Servicio

# Multiplicador segun la experiencia del consultor asignado
NIVELES = {"junior": 1.0, "senior": 1.4, "experto": 1.8}


class ServicioAsesoria(Servicio):
    """Asesoria profesional dictada por un consultor."""

    prefijo = "ASE"
    unidad = "hora"
    duracion_minima = 1
    duracion_maxima = 8

    def __init__(self, nombre, costo_base, especialidad, nivel="junior", disponible=True):
        super().__init__(nombre, costo_base, disponible)
        self.especialidad = especialidad
        self.nivel = nivel

    @property
    def especialidad(self):
        return self._especialidad

    @especialidad.setter
    def especialidad(self, valor):
        texto = " ".join(str(valor).split()) if valor else ""
        if len(texto) < 3:
            raise ErrorValidacion(f"Especialidad invalida: {texto!r} (minimo 3 caracteres).")
        self._especialidad = texto

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        texto = str(valor).strip().lower() if valor else ""
        if texto not in NIVELES:
            raise ErrorValidacion(
                f"Nivel de consultor {texto!r} no valido. Opciones: {', '.join(NIVELES)}."
            )
        self._nivel = texto

    @property
    def multiplicador(self):
        return NIVELES[self._nivel]

    # ---------------- metodos sobrescritos (polimorfismo) ----------------
    def validar_parametros(self, duracion):
        horas = self._validar_duracion(duracion)
        if self._nivel == "experto" and horas < 2:
            raise ErrorValidacion("Las asesorias con consultor experto requieren minimo 2 horas.")
        return horas

    def calcular_costo(self, duracion):
        horas = self.validar_parametros(duracion)
        return round(self.costo_base * horas * self.multiplicador, 2)

    def describir(self):
        return (
            f"{super().describir()} | especialidad {self._especialidad} "
            f"| consultor {self._nivel} (x{self.multiplicador})"
        )
