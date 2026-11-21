"""
Clase abstracta Servicio: base de todos los servicios de Software FJ.

Define el contrato polimorfico (calcular_costo, validar_parametros,
describir) y las variantes sobrecargadas del calculo de costos.
"""
from abc import abstractmethod
from functools import singledispatchmethod

from excepciones.errores import (
    ErrorCalculoCosto,
    ErrorServicioNoDisponible,
    ErrorSistemaFJ,
    ErrorValidacion,
)
from modelo.entidad import EntidadBase

IVA = 0.19  # impuesto aplicado por defecto


class Servicio(EntidadBase):
    """Servicio generico de la empresa. No se instancia directamente."""

    prefijo = "SRV"
    unidad = "unidad"
    duracion_minima = 1
    duracion_maxima = 24

    def __init__(self, nombre, costo_base, disponible=True):
        super().__init__()
        self.nombre = nombre
        self.costo_base = costo_base
        self._disponible = bool(disponible)

    # ------------------- propiedades encapsuladas -------------------
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor is None or not str(valor).strip():
            raise ErrorValidacion("El nombre del servicio es obligatorio.")
        texto = " ".join(str(valor).split())
        if len(texto) < 3:
            raise ErrorValidacion("El nombre del servicio debe tener al menos 3 caracteres.")
        self._nombre = texto

    @property
    def costo_base(self):
        return self._costo_base

    @costo_base.setter
    def costo_base(self, valor):
        try:
            numero = float(valor)
        except (TypeError, ValueError) as exc:
            # encadenamiento de excepciones: se conserva la causa original
            raise ErrorValidacion(f"Costo base no numerico: {valor!r}.") from exc
        if numero <= 0:
            raise ErrorValidacion(f"El costo base debe ser mayor que cero (se recibio {numero}).")
        self._costo_base = round(numero, 2)

    @property
    def disponible(self):
        return self._disponible

    def cambiar_disponibilidad(self, estado):
        self._disponible = bool(estado)
        return self._disponible

    def verificar_disponibilidad(self):
        if not self._disponible:
            raise ErrorServicioNoDisponible(
                f"El servicio {self._nombre!r} ({self._identificador}) no esta disponible."
            )
        return True

    # --------------------- contrato polimorfico ---------------------
    @abstractmethod
    def calcular_costo(self, duracion):
        """Costo neto del servicio; cada especializacion lo sobrescribe."""

    @abstractmethod
    def validar_parametros(self, duracion):
        """Valida la duracion y los parametros propios del servicio."""

    def validar(self):
        self.verificar_disponibilidad()
        return True

    def describir(self):
        estado = "disponible" if self._disponible else "NO disponible"
        return (
            f"{type(self).__name__} {self._nombre!r} | base ${self._costo_base:,.2f} "
            f"por {self.unidad} | {estado}"
        )

    # ------------------- validacion compartida -------------------
    def _validar_duracion(self, duracion):
        """Validacion comun de duracion, reutilizada por las clases hijas."""
        if duracion is None or duracion == "":
            raise ErrorValidacion("Parametro faltante: la duracion es obligatoria.")
        try:
            valor = int(duracion)
        except (TypeError, ValueError) as exc:
            raise ErrorValidacion(f"Duracion no numerica: {duracion!r}.") from exc
        if not self.duracion_minima <= valor <= self.duracion_maxima:
            raise ErrorValidacion(
                f"Duracion de {valor} {self.unidad}(s) fuera de rango para "
                f"{self._nombre}: permitido {self.duracion_minima}-{self.duracion_maxima}."
            )
        return valor

    # ---------------- sobrecarga por parametros opcionales ----------------
    def calcular_total(self, duracion, impuesto=None, descuento=0.0, extras=None):
        """
        Variante sobrecargada del calculo de costos:

        - calcular_total(4)                         -> costo + IVA por defecto
        - calcular_total(4, impuesto=0.0)           -> sin impuestos
        - calcular_total(4, descuento=0.10)         -> con descuento
        - calcular_total(4, extras={"soporte": 50}) -> con cargos adicionales
        """
        impuesto = IVA if impuesto is None else impuesto
        try:
            impuesto = float(impuesto)
            descuento = float(descuento if descuento is not None else 0.0)
        except (TypeError, ValueError) as exc:
            raise ErrorCalculoCosto("Impuesto o descuento no numericos.") from exc

        if not 0.0 <= impuesto <= 1.0:
            raise ErrorCalculoCosto(f"Impuesto fuera del rango 0-1: {impuesto}.")
        if not 0.0 <= descuento <= 0.5:
            raise ErrorCalculoCosto(f"Descuento fuera del rango 0-0.5: {descuento}.")

        self.verificar_disponibilidad()
        self.validar_parametros(duracion)

        try:
            subtotal = float(self.calcular_costo(duracion))
        except ErrorSistemaFJ:
            raise
        except Exception as exc:
            raise ErrorCalculoCosto(
                f"Fallo inesperado calculando el costo de {self._nombre}."
            ) from exc

        adicionales = 0.0
        for concepto, valor in (extras or {}).items():
            try:
                adicionales += float(valor)
            except (TypeError, ValueError) as exc:
                raise ErrorCalculoCosto(
                    f"Cargo adicional invalido {concepto!r}: {valor!r}."
                ) from exc

        neto = subtotal + adicionales
        total = (neto - neto * descuento) * (1 + impuesto)
        if total < 0:
            raise ErrorCalculoCosto(f"Calculo inconsistente: total negativo ({total:.2f}).")
        return round(total, 2)

    def desglose(self, duracion, impuesto=None, descuento=0.0, extras=None):
        """Detalle del cobro; lo usa la interfaz grafica para mostrar la cotizacion."""
        tasa = IVA if impuesto is None else float(impuesto)
        subtotal = round(float(self.calcular_costo(self._validar_duracion(duracion))), 2)
        adicionales = round(sum(float(v) for v in (extras or {}).values()), 2)
        neto = subtotal + adicionales
        valor_descuento = round(neto * float(descuento or 0.0), 2)
        base = neto - valor_descuento
        return {
            "subtotal": subtotal,
            "adicionales": adicionales,
            "descuento": valor_descuento,
            "impuesto": round(base * tasa, 2),
            "total": self.calcular_total(duracion, tasa, descuento, extras),
        }

    # --------- sobrecarga por tipo de argumento (singledispatchmethod) ---------
    @singledispatchmethod
    def cotizar(self, valor):
        """Cotiza segun el tipo de dato recibido (sobrecarga por tipo)."""
        raise ErrorCalculoCosto(
            f"No se puede cotizar con un argumento de tipo {type(valor).__name__}."
        )

    @cotizar.register(int)
    def _(self, duracion):
        """cotizar(3) -> total de una sola duracion."""
        return self.calcular_total(duracion)

    @cotizar.register(float)
    def _(self, duracion):
        """cotizar(3.0) -> se redondea a unidades enteras."""
        return self.calcular_total(int(round(duracion)))

    @cotizar.register(list)
    @cotizar.register(tuple)
    def _(self, duraciones):
        """cotizar([2, 4]) -> suma de varias duraciones (paquete de servicios)."""
        if not duraciones:
            raise ErrorCalculoCosto("La lista de duraciones esta vacia.")
        return round(sum(self.calcular_total(d) for d in duraciones), 2)

    @cotizar.register(dict)
    def _(self, parametros):
        """cotizar({'duracion': 4, 'descuento': 0.1}) -> cotizacion parametrizada."""
        if "duracion" not in parametros:
            raise ErrorCalculoCosto("Parametro faltante 'duracion' en la cotizacion.")
        return self.calcular_total(
            parametros["duracion"],
            parametros.get("impuesto"),
            parametros.get("descuento", 0.0),
            parametros.get("extras"),
        )
