"""Clase abstracta que representa cualquier entidad general del sistema."""
from abc import ABC, abstractmethod
from datetime import datetime

from excepciones.errores import ErrorValidacion


class EntidadBase(ABC):
    """
    Abstraccion comun a clientes, servicios y reservas.

    Aporta identificador automatico, fecha de creacion y obliga a que
    cada entidad concreta implemente describir() y validar().
    """

    prefijo = "ENT"
    _contadores = {}

    def __init__(self, identificador=None):
        if identificador is None:
            identificador = self._generar_id()
        elif not str(identificador).strip():
            raise ErrorValidacion("El identificador de la entidad no puede estar vacio.")
        self._identificador = str(identificador).strip().upper()
        self._creado_en = datetime.now()

    @classmethod
    def _generar_id(cls):
        consecutivo = EntidadBase._contadores.get(cls.prefijo, 0) + 1
        EntidadBase._contadores[cls.prefijo] = consecutivo
        return f"{cls.prefijo}-{consecutivo:03d}"

    # ---- encapsulacion: solo lectura desde fuera ----
    @property
    def identificador(self):
        return self._identificador

    @property
    def creado_en(self):
        return self._creado_en

    # ---- contrato abstracto (polimorfismo) ----
    @abstractmethod
    def describir(self):
        """Texto descriptivo propio de cada entidad."""

    @abstractmethod
    def validar(self):
        """Valida el estado interno. Lanza ErrorValidacion si algo falla."""

    def resumen(self):
        return f"[{self._identificador}] {self.describir()}"

    def __str__(self):
        return self.resumen()

    def __repr__(self):
        return f"<{type(self).__name__} {self._identificador}>"

    def __eq__(self, otro):
        return isinstance(otro, EntidadBase) and self._identificador == otro.identificador

    def __hash__(self):
        return hash(self._identificador)
