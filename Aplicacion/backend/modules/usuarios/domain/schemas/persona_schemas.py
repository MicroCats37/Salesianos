"""
DTOs internos (Pydantic) del módulo `usuarios`.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.1 y §3.

Reflejan lo que la capa de servicios necesita, NO lo que el cliente HTTP
envía (`contract/django-app-architecture-contract.md` §4.6).

Aquí viven también las reglas de NORMALIZACIÓN del documento, que son la
única validación del dato en la capa de dominio
(`contract/django-app-architecture-contract.md` §10 — no duplicar la
validación entre modelo, servicio y HTTP).
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from modules.usuarios.domain.constants import OrigenDatosChoices, TipoDocumentoChoices
from modules.usuarios.domain.exceptions import TipoDocumentoInvalidoError

#: Separadores que se eliminan del documento antes de persistirlo.
_SEPARADORES_DOCUMENTO = re.compile(r"[\s\-./_]")


def normalizar_numero_documento(valor: str) -> str:
    """Documento normalizado: sin espacios ni separadores, en mayúsculas.

    La comparación es case-insensitive POR CONSTRUCCIÓN: el valor persistido
    siempre está normalizado, así que la igualdad basta
    (`FR-03` §1.1 — "case-insensitive en la comparación").
    """
    return _SEPARADORES_DOCUMENTO.sub("", str(valor or "")).upper()


def normalizar_tipo_documento(valor: str) -> str:
    """Tipo de documento canónico del vocabulario cerrado.

    Lanza `TipoDocumentoInvalidoError` (422) si el valor no pertenece al
    vocabulario: un tipo inventado es un error, nunca un dato a guardar.
    """
    candidato = str(valor or "").strip().upper()
    validos = {choice.value for choice in TipoDocumentoChoices}
    if candidato not in validos:
        raise TipoDocumentoInvalidoError()
    return candidato


class PersonaCreateData(BaseModel):
    """Datos de alta de una `Persona` (uso interno del servicio)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str = ""
    genero: str = ""
    telefono: str = ""
    whatsapp: str = ""
    contacto_emergencia_nombre: str = ""
    contacto_emergencia_telefono: str = ""
    origen_datos: str = OrigenDatosChoices.LOCAL.value
    datos_obtenidos_en: datetime | None = None

    @field_validator("tipo_documento")
    @classmethod
    def _validar_tipo(cls, valor: str) -> str:
        return normalizar_tipo_documento(valor)

    @field_validator("numero_documento")
    @classmethod
    def _normalizar_documento(cls, valor: str) -> str:
        return normalizar_numero_documento(valor)

    @field_validator("nombres")
    @classmethod
    def _exigir_nombres(cls, valor: str) -> str:
        if not str(valor or "").strip():
            raise ValueError("El nombre de la persona es obligatorio.")
        return str(valor).strip()


class PersonaConfirmarData(BaseModel):
    """Confirmación de una identidad (operación real que sí persiste).

    Es el ÚNICO camino que escribe una `Persona` derivada de la fuente
    externa (`FR-03` §3.2 regla 2 — persistencia diferida).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str = ""
    genero: str = ""
    origen_datos: str = OrigenDatosChoices.EXTERNO.value
    datos_obtenidos_en: datetime | None = None

    @field_validator("tipo_documento")
    @classmethod
    def _validar_tipo(cls, valor: str) -> str:
        return normalizar_tipo_documento(valor)

    @field_validator("numero_documento")
    @classmethod
    def _normalizar_documento(cls, valor: str) -> str:
        return normalizar_numero_documento(valor)

    @field_validator("nombres")
    @classmethod
    def _exigir_nombres(cls, valor: str) -> str:
        if not str(valor or "").strip():
            raise ValueError("El nombre de la persona es obligatorio.")
        return str(valor).strip()


__all__ = [
    "PersonaConfirmarData",
    "PersonaCreateData",
    "normalizar_numero_documento",
    "normalizar_tipo_documento",
]
