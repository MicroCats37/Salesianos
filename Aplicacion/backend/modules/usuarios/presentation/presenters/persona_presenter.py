"""
Presenters del módulo `usuarios`.

Freeze: `FREEZE-PS-1.0.0` (`FR-07` §4).

Reglas (`contract/PLAN_REFACTORIZACION.md` §3.A,
`contract/api-wrapper-presenter-contract.md` §3):

- El presenter TRANSFORMA un resultado de dominio en un schema HTTP.
- No consulta la base de datos, no llama a selectores y no elige mensajes.
- Sólo tiene métodos `@staticmethod` / `@classmethod`.

Los nombres de los presenters son los congelados en el ledger `RT-ID-*`:
`PersonaBusquedaPresenter`, `PersonaResolverPresenter` y
`PersonaConfirmarPresenter`.
"""

from modules.usuarios.domain.constants import OrigenResolucionChoices
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.results import (
    ConsultaDocumentoResultado,
    PersonaResolucionResult,
)
from modules.usuarios.presentation.schemas.persona_schemas import (
    DocumentoConsultaOut,
    PersonaOut,
    PersonaResueltaOut,
)


class PersonaBusquedaPresenter:
    """Presenter de la consulta externa de documentos (`RT-ID-01`)."""

    @staticmethod
    def present_consulta(result: ConsultaDocumentoResultado) -> DocumentoConsultaOut:
        """Traduce el resultado de la fuente externa al wrapper HTTP."""
        return DocumentoConsultaOut(
            tipo_documento=result.tipo_documento,
            numero_documento=result.numero_documento,
            nombre_completo=result.nombre_completo,
        )


class PersonaResolverPresenter:
    """Presenter del resultado del resolver (`RT-ID-02`)."""

    @staticmethod
    def present_resolucion(result: PersonaResolucionResult) -> PersonaResueltaOut:
        """Traduce el resultado del resolver al wrapper HTTP.

        El origen viaja explícito: `LOCAL` (ya registrada) o `EXTERNO`
        (datos precargados y TODAVÍA SIN persistir).
        """
        if result.origen == OrigenResolucionChoices.LOCAL and result.persona:
            persona = result.persona
            return PersonaResueltaOut(
                origen=result.origen.value,
                persona_id=persona.id,
                persistida=True,
                tipo_documento=persona.tipo_documento,
                numero_documento=persona.numero_documento,
                nombres=persona.nombres,
                apellidos=persona.apellidos,
            )

        datos = result.datos
        return PersonaResueltaOut(
            origen=result.origen.value,
            persona_id=None,
            persistida=False,
            tipo_documento=datos.tipo_documento if datos else "",
            numero_documento=datos.numero_documento if datos else "",
            nombres=datos.nombres if datos else "",
            apellidos=datos.apellidos if datos else None,
        )


class PersonaConfirmarPresenter:
    """Presenter de la confirmación de una identidad (`RT-ID-03`)."""

    @staticmethod
    def present_persona(persona: Persona) -> PersonaOut:
        """Traduce la `Persona` persistida al wrapper HTTP."""
        return PersonaOut(
            id=persona.id,
            tipo_documento=persona.tipo_documento,
            numero_documento=persona.numero_documento,
            nombres=persona.nombres,
            apellidos=persona.apellidos,
            genero=persona.genero,
            origen_datos=persona.origen_datos,
            datos_obtenidos_en=persona.datos_obtenidos_en,
            creado_en=persona.created_at,
            actualizado_en=persona.updated_at,
        )


__all__ = [
    "PersonaBusquedaPresenter",
    "PersonaConfirmarPresenter",
    "PersonaResolverPresenter",
]
