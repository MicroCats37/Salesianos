"""
Core sync service of the rounds of the bracket.

A round groups the encounters played in the same stage of the elimination
tournament. Its label and its order are unique inside the competition and a
round is invalidated — never deleted — so the history of the bracket is
preserved.
"""
from ...constants import EstadoRondaChoices
from ...exceptions import (
    CompetenciaDuplicadaError,
    DeleteNotAllowedError,
    RondaNotFoundError,
)
from ...models import Competencia, Ronda
from ...schemas.competencias_schemas import RondaCreateData, RondaUpdateData
from .base_service import BaseCoreService
from .competencia_service import ESTADOS_TERMINALES_COMPETENCIA

#: A round can only be invalidated: there is no way back.
ESTADOS_TERMINALES_RONDA = {EstadoRondaChoices.INVALIDADA}


class RondaCoreService(BaseCoreService):
    """Sync operations over `Ronda` — the caller owns the transaction."""

    # ── reads ──────────────────────────────────────────────────────────────

    def obtener_por_id(self, ronda_id) -> Ronda:
        """Return the round or raise `RondaNotFoundError`."""
        try:
            return Ronda.objects.select_related("competencia").get(id=ronda_id)
        except (Ronda.DoesNotExist, ValueError, TypeError):
            raise RondaNotFoundError()

    # ── commands ───────────────────────────────────────────────────────────

    def crear(
        self,
        competencia: Competencia,
        data: RondaCreateData,
        actor=None,
    ) -> Ronda:
        """Create a round with a label and an order unique in the bracket."""
        self.exigir_no_terminal(competencia, ESTADOS_TERMINALES_COMPETENCIA)
        self._validar_unicidad(
            competencia=competencia,
            etiqueta=data.etiqueta,
            orden=data.orden,
        )
        ronda = Ronda(
            competencia=competencia,
            etiqueta=data.etiqueta.strip(),
            orden=data.orden,
            estado=EstadoRondaChoices.ACTIVA,
        )
        return self.persistir_nuevo(ronda, actor, "Alta de ronda en el cuadro")

    def actualizar(
        self,
        ronda: Ronda,
        data: RondaUpdateData,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Ronda:
        """Update the label or the order of the round."""
        self.exigir_no_terminal(ronda, ESTADOS_TERMINALES_RONDA)
        cambios = data.model_dump(exclude_none=True)
        if not cambios:
            return ronda
        ya_aplicado = all(
            getattr(ronda, campo) == valor for campo, valor in cambios.items()
        )
        self.aplicar_cas(ronda, expected_version, ya_aplicado)
        if ya_aplicado:
            return ronda

        self._validar_unicidad(
            competencia=ronda.competencia,
            etiqueta=cambios.get("etiqueta", ronda.etiqueta),
            orden=cambios.get("orden", ronda.orden),
            excluir_id=ronda.id,
        )
        if "etiqueta" in cambios:
            cambios["etiqueta"] = cambios["etiqueta"].strip()

        for campo, valor in cambios.items():
            setattr(ronda, campo, valor)
        return self.persistir_cambio(
            ronda, actor, motivo or "Actualización de la ronda"
        )

    def invalidar(
        self,
        ronda: Ronda,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Ronda:
        """Invalidate the round: the encounters and the history are kept."""
        if ronda.estado == EstadoRondaChoices.INVALIDADA:
            return ronda
        self.exigir_no_terminal(ronda, ESTADOS_TERMINALES_RONDA)
        self.aplicar_cas(ronda, expected_version)
        ronda.estado = EstadoRondaChoices.INVALIDADA
        return self.persistir_cambio(
            ronda, actor, motivo or "Invalidación de la ronda"
        )

    def eliminar(self, ronda: Ronda, actor=None) -> None:
        """Physically delete a round that was never used.

        A round with encounters, with a change after its creation or that is
        not active cannot be deleted: it must be invalidated instead.
        """
        if ronda.estado != EstadoRondaChoices.ACTIVA:
            raise DeleteNotAllowedError()
        if ronda.encuentros.exists():
            raise DeleteNotAllowedError()
        if ronda.history.count() > 1:
            raise DeleteNotAllowedError()
        ronda.delete()

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _validar_unicidad(
        competencia: Competencia,
        etiqueta: str,
        orden: int,
        excluir_id=None,
    ) -> None:
        """The label and the order of a round are unique in the bracket."""
        consultas = Ronda.objects.filter(competencia=competencia)
        if excluir_id is not None:
            consultas = consultas.exclude(id=excluir_id)
        if consultas.filter(etiqueta=(etiqueta or "").strip()).exists():
            raise CompetenciaDuplicadaError()
        if consultas.filter(orden=orden).exists():
            raise CompetenciaDuplicadaError()
