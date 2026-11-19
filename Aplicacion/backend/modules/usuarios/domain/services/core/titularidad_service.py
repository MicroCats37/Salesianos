"""
`TitularidadService` — interfaz de titularidad congelada.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §2 · `RN-U02` · `RN-U04`.

Reglas de la interfaz (`FR-03` §2.1):

1. La comprobación de titularidad es una función del MÓDULO DUEÑO del
   recurso. Este módulo NO consulta modelos de otros módulos: expone
   primitivas puras y el vocabulary; cada módulo (DOM-01…DOM-08) comprueba
   sobre SU recurso.
2. Prohibido inferir titularidad del conocimiento del documento (`RN-U04`).
   Por eso la `Persona` sujeto SIEMPRE sale de `persona_del_actor(usuario)`:
   la cuenta autenticada. Un documento resuelto NUNCA es el sujeto.
3. El grupo NO sustituye la titularidad: ser `Administrador` no convierte a
   alguien en responsable de una inscripción ajena.
4. Un fallo de titularidad responde 403 con código estable
   (`ACCESO_NO_AUTORIZADO`) y nunca revela la existencia del recurso de otro
   actor: el módulo dueño responde 404 cuando revelar el recurso ya sería una
   fuga.
"""

from dataclasses import dataclass
from typing import Optional

from modules.usuarios.domain.constants import TitularidadChoices
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService

#: Motivos internos de un rechazo. Son técnicos: no salen al cliente.
MOTIVO_SIN_PERSONA = "SIN_PERSONA_VINCULADA"
MOTIVO_NO_TITULAR = "NO_ES_TITULAR"
MOTIVO_DERECHO_REVOCADO = "DERECHO_REVOCADO"
MOTIVO_ES_ADMIN = "ES_ADMINISTRADOR"


@dataclass(frozen=True)
class RecursoTitularidad:
    """Vista MÍNIMA del recurso que aporta el módulo dueño.

    Cada módulo construye esta vista con los identificadores de SU recurso.
    El módulo de identidad no conoce `Inscripcion`, `Compra` ni
    `PaseBeneficiario`: sólo compara identificadores.
    """

    responsable_id: Optional[str] = None
    persona_id: Optional[str] = None
    derecho_revocado: bool = False


@dataclass(frozen=True)
class TitularidadResultado:
    """Veredicto de una comprobación de titularidad."""

    titularidad: str
    permitida: bool
    motivo: str


class TitularidadService:
    """Primitivas de titularidad reutilizables por los módulos dueños."""

    def __init__(self, grupo_service: GrupoFuncionalService | None = None):
        self.grupo_service = grupo_service or GrupoFuncionalService()

    # ── Sujeto ──────────────────────────────────────────────────────────────

    def persona_del_actor(self, usuario) -> Optional[Persona]:
        """La `Persona` vinculada a la cuenta autenticada, o `None`.

        Éste es el ÚNICO origen admisible del sujeto de una titularidad: de
        aquí sale la identidad que se compara con el recurso.
        """
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return None
        persona = getattr(usuario, "persona_fk", None)
        return persona

    # ── Comprobaciones por titularidad ─────────────────────────────────────

    def es_responsable(self, persona: Optional[Persona], recurso: RecursoTitularidad) -> bool:
        """`TITULARIDAD_RESPONSABLE`: el sujeto es el responsable del recurso."""
        if persona is None or recurso.responsable_id is None:
            return False
        return str(recurso.responsable_id) == str(persona.id)

    def es_comprador(self, persona: Optional[Persona], recurso: RecursoTitularidad) -> bool:
        """`TITULARIDAD_COMPRADOR`: el sujeto es el comprador del recurso."""
        if persona is None or recurso.persona_id is None:
            return False
        return str(recurso.persona_id) == str(persona.id)

    def es_beneficiario(
        self,
        persona: Optional[Persona],
        recurso: RecursoTitularidad,
    ) -> bool:
        """`TITULARIDAD_BENEFICIARIO`: el sujeto es el beneficiario y el
        derecho NO está revocado."""
        if not self.es_comprador(persona, recurso):
            return False
        return not recurso.derecho_revocado

    def es_admin(self, usuario) -> bool:
        """`TITULARIDAD_ADMIN`: la cuenta pertenece al grupo `Administrador`."""
        return self.grupo_service.es_administrador(usuario)

    # ── Veredicto ──────────────────────────────────────────────────────────

    def verificar(
        self,
        *,
        titularidad: str,
        usuario,
        recurso: RecursoTitularidad,
    ) -> TitularidadResultado:
        """Verifica una titularidad y devuelve el veredicto con su motivo.

        La autoridad del grupo (`Administrador`) PERMITE la operación, pero
        no sustituye la titularidad: un administrador no es el responsable de
        una inscripción ajena (`FR-03` §2.1 regla 3).
        """
        try:
            tipo = TitularidadChoices(titularidad)
        except ValueError:
            return TitularidadResultado(
                titularidad=titularidad,
                permitida=False,
                motivo=MOTIVO_NO_TITULAR,
            )

        if tipo == TitularidadChoices.ADMIN:
            permitida = self.es_admin(usuario)
            return TitularidadResultado(
                titularidad=tipo.value,
                permitida=permitida,
                motivo=MOTIVO_ES_ADMIN if permitida else MOTIVO_NO_TITULAR,
            )

        persona = self.persona_del_actor(usuario)
        if persona is None:
            return TitularidadResultado(
                titularidad=tipo.value,
                permitida=False,
                motivo=MOTIVO_SIN_PERSONA,
            )

        if tipo == TitularidadChoices.RESPONSABLE:
            permitida = self.es_responsable(persona, recurso)
        elif tipo == TitularidadChoices.COMPRADOR:
            permitida = self.es_comprador(persona, recurso)
        else:
            permitida = self.es_beneficiario(persona, recurso)

        if not permitida:
            motivo = (
                MOTIVO_DERECHO_REVOCADO
                if recurso.derecho_revocado
                else MOTIVO_NO_TITULAR
            )
        else:
            motivo = MOTIVO_NO_TITULAR

        return TitularidadResultado(
            titularidad=tipo.value,
            permitida=permitida,
            motivo=motivo,
        )


__all__ = [
    "MOTIVO_DERECHO_REVOCADO",
    "MOTIVO_ES_ADMIN",
    "MOTIVO_NO_TITULAR",
    "MOTIVO_SIN_PERSONA",
    "RecursoTitularidad",
    "TitularidadResultado",
    "TitularidadService",
]
