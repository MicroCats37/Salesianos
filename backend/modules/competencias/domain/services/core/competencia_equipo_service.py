"""
Core sync service of the participation of a team inside the bracket.

`CompetenciaEquipo` is the bridge between the team of the enrollment domain
(`Equipo`) and the bracket. It carries the MANUAL seed/order and the state
of the participation (active or withdrawn).

Eligibility (design): the team must be active and its enrollment, discipline
and category must be the ones of the competition. The roster of the team is
an upstream invariant and is NOT validated here.
"""
from modules.salesianos_fest.domain.constants import EstadoEquipoChoices
from modules.salesianos_fest.domain.models import Equipo

from ...constants import EstadoCompetenciaEquipoChoices
from ...exceptions import (
    CompetenciaDuplicadaError,
    CompetenciaEquipoNotFoundError,
    EquipoNoElegibleError,
    InvalidStateTransitionError,
)
from ...models import Competencia, CompetenciaEquipo
from ...schemas.competencias_schemas import CompetenciaEquipoUpdateData
from .base_service import BaseCoreService
from .competencia_service import ESTADOS_TERMINALES_COMPETENCIA


class CompetenciaEquipoCoreService(BaseCoreService):
    """Sync operations over `CompetenciaEquipo` — no transaction of its own."""

    # ── reads ──────────────────────────────────────────────────────────────

    def obtener_por_id(self, competencia_equipo_id) -> CompetenciaEquipo:
        """Return the entry of the bracket or raise the not-found error."""
        try:
            return CompetenciaEquipo.objects.select_related(
                "competencia",
                "equipo",
            ).get(id=competencia_equipo_id)
        except (CompetenciaEquipo.DoesNotExist, ValueError, TypeError):
            raise CompetenciaEquipoNotFoundError()

    def es_elegible(self, equipo: Equipo, competencia: Competencia) -> bool:
        """True when the team may compete in the competition.

        The team must be active, its enrollment must belong to the event of
        the competition and it must play the same discipline and category.
        """
        if equipo.estado != EstadoEquipoChoices.EQUIPO_ACTIVO:
            return False
        if equipo.categoria_id is None:
            return False
        return (
            equipo.inscripcion.evento_id == competencia.evento_id
            and equipo.disciplina_id == competencia.disciplina_id
            and equipo.categoria_id == competencia.categoria_id
        )

    # ── commands ───────────────────────────────────────────────────────────

    def incorporar(
        self,
        competencia: Competencia,
        equipo_id,
        orden: int,
        actor=None,
    ) -> CompetenciaEquipo:
        """Register a team in the bracket with its manual order."""
        self.exigir_no_terminal(competencia, ESTADOS_TERMINALES_COMPETENCIA)
        equipo = self._obtener_equipo(equipo_id)
        if not self.es_elegible(equipo, competencia):
            raise EquipoNoElegibleError()
        if CompetenciaEquipo.objects.filter(
            competencia=competencia,
            equipo=equipo,
        ).exists():
            raise EquipoNoElegibleError()
        if CompetenciaEquipo.objects.filter(
            competencia=competencia,
            orden=orden,
            estado=EstadoCompetenciaEquipoChoices.ACTIVO,
        ).exists():
            raise CompetenciaDuplicadaError()

        entrada = CompetenciaEquipo(
            competencia=competencia,
            equipo=equipo,
            orden=orden,
            estado=EstadoCompetenciaEquipoChoices.ACTIVO,
        )
        return self.persistir_nuevo(
            entrada, actor, "Alta de equipo en la competencia"
        )

    def actualizar(
        self,
        entrada: CompetenciaEquipo,
        data: CompetenciaEquipoUpdateData,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> CompetenciaEquipo:
        """Update the manual order or the state of the participation."""
        cambios = data.model_dump(exclude_none=True)
        if not cambios:
            return entrada
        ya_aplicado = all(
            getattr(entrada, campo) == valor for campo, valor in cambios.items()
        )
        self.aplicar_cas(entrada, expected_version, ya_aplicado)
        if ya_aplicado:
            return entrada

        if "orden" in cambios:
            # The manual order is an audited decision of the administrator.
            motivo = self.exigir_motivo(motivo)
            self._validar_orden(entrada, cambios["orden"])
        if "estado" in cambios:
            self._validar_estado(entrada, cambios["estado"])

        for campo, valor in cambios.items():
            setattr(entrada, campo, valor)
        return self.persistir_cambio(
            entrada, actor, motivo or "Actualización del equipo de la competencia"
        )

    def retirar(
        self,
        entrada: CompetenciaEquipo,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> CompetenciaEquipo:
        """Withdraw the team from the bracket (the history is preserved)."""
        if entrada.estado != EstadoCompetenciaEquipoChoices.ACTIVO:
            raise InvalidStateTransitionError()
        self.aplicar_cas(entrada, expected_version)
        entrada.estado = EstadoCompetenciaEquipoChoices.RETIRADO
        return self.persistir_cambio(
            entrada, actor, motivo or "Retiro del equipo de la competencia"
        )

    def reactivar(
        self,
        entrada: CompetenciaEquipo,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> CompetenciaEquipo:
        """Bring a withdrawn team back into the bracket."""
        if entrada.estado != EstadoCompetenciaEquipoChoices.RETIRADO:
            raise InvalidStateTransitionError()
        self.aplicar_cas(entrada, expected_version)
        self._validar_orden(entrada, entrada.orden)
        entrada.estado = EstadoCompetenciaEquipoChoices.ACTIVO
        return self.persistir_cambio(
            entrada, actor, motivo or "Reactivación del equipo de la competencia"
        )

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _obtener_equipo(equipo_id) -> Equipo:
        try:
            return Equipo.objects.select_related(
                "inscripcion",
                "disciplina",
                "categoria",
            ).get(id=equipo_id)
        except (Equipo.DoesNotExist, ValueError, TypeError):
            raise EquipoNoElegibleError()

    @staticmethod
    def _validar_orden(entrada: CompetenciaEquipo, orden: int) -> None:
        """The manual order is unique among the ACTIVE entries."""
        duplicado = CompetenciaEquipo.objects.filter(
            competencia_id=entrada.competencia_id,
            orden=orden,
            estado=EstadoCompetenciaEquipoChoices.ACTIVO,
        )
        if entrada.pk:
            duplicado = duplicado.exclude(pk=entrada.pk)
        if duplicado.exists():
            raise CompetenciaDuplicadaError()

    @staticmethod
    def _validar_estado(entrada: CompetenciaEquipo, estado: str) -> None:
        if estado not in EstadoCompetenciaEquipoChoices.values:
            raise InvalidStateTransitionError()
