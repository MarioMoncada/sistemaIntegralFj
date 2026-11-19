"""Clase Cliente con encapsulacion y validaciones estrictas."""
import re

from excepciones.errores import ErrorValidacion
from modelo.entidad import EntidadBase

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _nombre_valido(texto):
    """Acepta letras (con tildes), espacios y los signos . ' - de los nombres."""
    return 3 <= len(texto) <= 60 and all(c.isalpha() or c in " '-." for c in texto)

# Descuento comercial asociado a cada categoria de cliente
CATEGORIAS = {"regular": 0.0, "premium": 0.10, "corporativo": 0.15}


class Cliente(EntidadBase):
    """Cliente de Software FJ. Sus datos personales estan encapsulados."""

    prefijo = "CLI"

    def __init__(self, nombre, documento, email, telefono, categoria="regular"):
        super().__init__()
        # los setters realizan la validacion de cada dato
        self.nombre = nombre
        self.documento = documento
        self.email = email
        self.telefono = telefono
        self.categoria = categoria
        self._historial = []
        self.validar()

    # ------------------- propiedades encapsuladas -------------------
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor is None or not str(valor).strip():
            raise ErrorValidacion("El nombre del cliente es obligatorio.")
        texto = " ".join(str(valor).split())
        if not _nombre_valido(texto):
            raise ErrorValidacion(f"Nombre invalido: '{texto}' (solo letras, minimo 3 caracteres).")
        self._nombre = texto.title()

    @property
    def documento(self):
        return self._documento

    @documento.setter
    def documento(self, valor):
        texto = str(valor).strip() if valor is not None else ""
        if not texto.isdigit():
            raise ErrorValidacion(f"El documento debe ser numerico, se recibio '{texto}'.")
        if not 6 <= len(texto) <= 15:
            raise ErrorValidacion("El documento debe tener entre 6 y 15 digitos.")
        self._documento = texto

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        texto = str(valor).strip().lower() if valor is not None else ""
        if not PATRON_EMAIL.match(texto):
            raise ErrorValidacion(f"Correo electronico invalido: '{texto}'.")
        self._email = texto

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        texto = str(valor).strip().replace(" ", "") if valor is not None else ""
        limpio = texto[1:] if texto.startswith("+") else texto
        if not limpio.isdigit() or not 7 <= len(limpio) <= 15:
            raise ErrorValidacion(f"Telefono invalido: '{texto}' (7 a 15 digitos).")
        self._telefono = texto

    @property
    def categoria(self):
        return self._categoria

    @categoria.setter
    def categoria(self, valor):
        texto = str(valor).strip().lower() if valor is not None else "regular"
        if texto not in CATEGORIAS:
            raise ErrorValidacion(
                f"Categoria '{texto}' no valida. Opciones: {', '.join(CATEGORIAS)}."
            )
        self._categoria = texto

    @property
    def historial(self):
        """Copia inmutable del historial: no se expone la lista interna."""
        return tuple(self._historial)

    # ------------------------- comportamiento -------------------------
    def descuento_por_categoria(self):
        return CATEGORIAS[self._categoria]

    def registrar_en_historial(self, texto):
        self._historial.append(str(texto))

    def describir(self):
        return (
            f"Cliente {self._nombre} | doc. {self._documento} | {self._email} "
            f"| tel. {self._telefono} | categoria {self._categoria} "
            f"(descuento {self.descuento_por_categoria():.0%})"
        )

    def validar(self):
        """Revalida el objeto completo; util antes de guardarlo en el sistema."""
        faltantes = [
            campo
            for campo in ("_nombre", "_documento", "_email", "_telefono", "_categoria")
            if not getattr(self, campo, None)
        ]
        if faltantes:
            raise ErrorValidacion(f"Cliente incompleto, faltan datos: {faltantes}")
        return True
