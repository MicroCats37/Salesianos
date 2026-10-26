"""
Core sync service of the competition — the aggregate root of the bracket.

The competition owns the identity of the bracket (event + discipline +
category + name), its single date and its lifecycle. Every rule lives here:
the models stay anemic (contract/django-app-architecture-contract.md §6).

The service is SYNC and never opens a transaction: the flow owns the
atomicity (contract §4.3).
"""
from django.db.models.functions import Lower

from core.exceptions import NotFoundError
from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import Categoria, Disciplina

from ...constants import EstadoCompetenciaChoices
from ...exceptions import (
    CompetenciaDuplicadaError,
    CompetenciaNotFoundError,
    DeleteNotAllowedError,
    InvalidScheduleError,
    InvalidStateTransitionError,
)
from ...models import Competencia
from ...schemas.competencias_schemas import (
    CompetenciaCreateData,
    CompetenciaUpdateData,
)
from .base_service import BaseCoreService


#: Legal transitions of the competition (spec: PLANIFICADA → EN_CURSO →
#: FINALIZADA; it MAY be cancelled before finishing and then it is terminal).
TRANSICIONES_COMPETENCIA: dict[str, set[str]] = {
    EstadoCompetenciaChoices.PLANIFICADA: {
        EstadoCompetenciaChoices.EN_CURSO,
        EstadoCompetenciaChoices.CANCELADA,
    },
    EstadoCompetenciaChoices.EN_CURSO: {
        EstadoCompetenciaChoices.FINALIZADA,
        EstadoCompetenciaChoices.CANCELADA,
    },
    EstadoCompetenciaChoices.FINALIZADA: set(),
    EstadoCompetenciaChoices.CANCELADA: set(),
}

#: States after which the competition no longer accepts changes.
ESTADOS_TERMINALES_COMPETENCIA = {
    EstadoCompetenciaChoices.FINALIZADA,
    EstadoCompetenciaChoices.CANCELADA,
}


class CompetenciaCoreService(BaseCoreService):
    """Sync operations over `Competencia` — the caller owns the transaction."""

    # ── reads ──────────────────────────────────────────────────────────────

    def obtener_por_id(self, competencia_id) -> Competencia:
        """Return the competition or raise `CompetenciaNotFoundError`."""
        try:
            return Competencia.objects.select_related(
                "evento",
                "disciplina",
                "categoria",
            ).get(id=competencia_id)
        except (Competencia.DoesNotExist, ValueError, TypeError):
            raise CompetenciaNotFoundError()

    # ── commands ───────────────────────────────────────────────────────────

    def crear(self, data: CompetenciaCreateData, actor=None) -> Competencia:
        """Create the competition with its identity and its single date."""
        evento = self._obtener_evento(data.evento_id)
        self._obtener_disciplina(data.disciplina_id)
        self._obtener_categoria(data.categoria_id)
        self._validar_fecha_dentro_del_evento(evento, data.fecha)
        self._validar_identidad(
            evento_id=data.evento_id,
            disciplina_id=data.disciplina_id,
            categoria_id=data.categoria_id,
            nombre=data.nombre,
        )
        competencia = Competencia(
            evento_id=data.evento_id,
            disciplina_id=data.disciplina_id,
            categoria_id=data.categoria_id,
            nombre=data.nombre.strip(),
            fecha=data.fecha,
            estado=EstadoCompetenciaChoices.PLANIFICADA,
        )
        return self.persistir_nuevo(
            competencia, actor, "Alta de la competencia"
        )

    def actualizar(
        self,
        competencia: Competencia,
        data: CompetenciaUpdateData,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Competencia:
        """Update the editable fields of the competition (name and date)."""
        self.exigir_no_terminal(competencia, ESTADOS_TERMINALES_COMPETENCIA)
        cambios = data.model_dump(exclude_none=True)
        if not cambios:
            return competencia

        ya_aplicado = all(
            getattr(competencia, campo) == valor for campo, valor in cambios.items()
        )
        self.aplicar_cas(competencia, expected_version, ya_aplicado)
        if ya_aplicado:
            return competencia

        if "fecha" in cambios:
            evento = self._obtener_evento(competencia.evento_id)
            self._validar_fecha_dentro_del_evento(evento, cambios["fecha"])
        if "nombre" in cambios:
            cambios["nombre"] = cambios["nombre"].strip()
            self._validar_identidad(
                evento_id=competencia.evento_id,
                disciplina_id=competencia.disciplina_id,
                categoria_id=competencia.categoria_id,
                nombre=cambios["nombre"],
                excluir_id=competencia.id,
            )

        for campo, valor in cambios.items():
            setattr(competencia, campo, valor)
        return self.persistir_cambio(
            competencia, actor, motivo or "Actualización de la competencia"
        )

    def cambiar_estado(
        self,
        competencia: Competencia,
        nuevo_estado: str,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Competencia:
        """Move the competition through its lifecycle.

        The transition is idempotent: asking for the state the competition
        already has does not write anything.
        """
        if competencia.estado == nuevo_estado:
            return competencia
        permitidos = TRANSICIONES_COMPETENCIA.get(competencia.estado, set())
        if nuevo_estado not in permitidos:
            raise InvalidStateTransitionError()
        self.aplicar_cas(competencia, expected_version)
        competencia.estado = nuevo_estado
        return self.persistir_cambio(
            competencia, actor, motivo or f"Cambio de estado a {nuevo_estado}"
        )

    def eliminar(self, competencia: Competencia, actor=None) -> None:
        """Physically delete a competition that was never used.

        Only a planned competition without teams, without rounds and without
        any change after its creation may be deleted. Everything else is
        cancelled or invalidated, keeping the history (design).
        """
        if competencia.estado != EstadoCompetenciaChoices.PLANIFICADA:
            raise DeleteNotAllowedError()
        if competencia.competencia_equipos.exists() or competencia.rondas.exists():
            raise DeleteNotAllowedError()
        if competencia.history.count() > 1:
            raise DeleteNotAllowedError()
        competencia.delete()

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _obtener_evento(evento_id) -> Evento:
        try:
            return Evento.objects.get(id=evento_id)
        except (Evento.DoesNotExist, ValueError, TypeError):
            raise NotFoundError(resource="Evento")

    @staticmethod
    def _obtener_disciplina(disciplina_id) -> Disciplina:
        try:
            return Disciplina.objects.get(id=disciplina_id)
        except (Disciplina.DoesNotExist, ValueError, TypeError):
            raise NotFoundError(resource="Disciplina")

    @staticmethod
    def _obtener_categoria(categoria_id) -> Categoria:
        try:
            return Categoria.objects.get(id=categoria_id)
        except (Categoria.DoesNotExist, ValueError, TypeError):
            raise NotFoundError(resource="Categoría")

    @staticmethod
    def _validar_fecha_dentro_del_evento(evento: Evento, fecha) -> None:
        """The competition happens on a single day inside its event."""
        if fecha is None:
            raise InvalidScheduleError()
        if not (evento.fecha_inicio <= fecha <= evento.fecha_fin):
            raise InvalidScheduleError()

    @staticmethod
    def _validar_identidad(
        evento_id,
        disciplina_id,
        categoria_id,
        nombre,
        excluir_id=None,
    ) -> None:
        """The identity of a competition is unique (case insensitive)."""
        consultas = Competencia.objects.filter(
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
        ).annotate(nombre_normalizado=Lower("nombre"))
        consultas = consultas.filter(
            nombre_normalizado=(nombre or "").strip().lower()
        )
        if excluir_id is not None:
            consultas = consultas.exclude(id=excluir_id)
        if consultas.exists():
            raise CompetenciaDuplicadaError()
