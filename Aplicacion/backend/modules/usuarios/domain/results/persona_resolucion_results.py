"""
Resultados de dominio del resolver local → fuente externa.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3.1.

Son DTOs de SALIDA de los servicios: no son esquemas HTTP y no conocen la
capa de presentación (`contract/django-app-architecture-contract.md` §4.6).
"""

from dataclasses import dataclass
from typing import Optional

from modules.usuarios.domain.constants import (
    EstadoConsultaDocumentoChoices,
    OrigenResolucionChoices,
)
from modules.usuarios.domain.models import Persona


@dataclass(frozen=True)
class PersonaDatosExternos:
    """Datos precargados desde la fuente externa, SIN persistir.

    `FR-03` §3.1 — el origen `EXTERNO` "no habilita escritura por sí solo".
    """

    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str = ""


@dataclass(frozen=True)
class ConsultaDocumentoResultado:
    """Respuesta TIPADA de la fuente externa de documentos.

    El estado distingue los cuatro fallos de `FR-03` §3.3. Un cliente
    (`contratos/03` §7) nunca fabrica identidades: como mucho informa que la
    fuente no está disponible.
    """

    estado: EstadoConsultaDocumentoChoices
    tipo_documento: str = ""
    numero_documento: str = ""
    nombre_completo: str = ""


@dataclass(frozen=True)
class PersonaResolucionResult:
    """Resultado del resolver con ORIGEN EXPLÍCITO (`FR-03` §3.1).

    | `origen` | `persona_id` | `datos` |
    |---|---|---|
    | `LOCAL` | id de la persona persistida | `None` |
    | `EXTERNO` | `None` | datos precargados, sin persistir |
    | `NO_ENCONTRADO` | `None` | `None` |
    | `FUENTE_NO_DISPONIBLE` | `None` | `None` |

    `estado` conserva el estado fino de la consulta externa (timeout frente a
    fuente caída frente a datos incompletos) para que el llamador pueda
    distinguir "reintentable" de "no existe" (`FR-03` §3.3).
    """

    origen: OrigenResolucionChoices
    persona: Optional[Persona] = None
    persona_id: Optional[str] = None
    datos: Optional[PersonaDatosExternos] = None
    estado: Optional[EstadoConsultaDocumentoChoices] = None

    @property
    def es_local(self) -> bool:
        return self.origen == OrigenResolucionChoices.LOCAL

    @property
    def es_externo(self) -> bool:
        return self.origen == OrigenResolucionChoices.EXTERNO


__all__ = [
    "ConsultaDocumentoResultado",
    "PersonaDatosExternos",
    "PersonaResolucionResult",
]
