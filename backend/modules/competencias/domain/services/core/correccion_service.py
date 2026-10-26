"""
Core sync service of the CORRECTION of the winner.

A correction NEVER cascades silently (design: "Nunca hay cascada silenciosa"):

- the `preview` traverses the links of the bracket and returns the IMPACT
  of the correction: which descendants would see their participant replaced
  and which derived results/advances would be cleaned,
- the `confirm` only applies the cascade when the descendants are still
  editable (they never started, they are not finished and they were not
  cancelled),
- when a descendant already started, finished or was cancelled, NOTHING
  changes unless the administrator sends an EXPLICIT override, accepts the
  impact and writes a motive (5..500).

The history of the encounters is never erased: the audit keeps the actor,
the motive, the date and the before/after of every change.
"""
from dataclasses import dataclass

from ...constants import CAMPOS_DE_SLOT, EstadoEncuentroChoices
from ...exceptions import DestinoBloqueadoError
from ...models import Encuentro
from ...results.competencias_results import (
    CorreccionPreviewResult,
    CorreccionResult,
    EncuentroResult,
    ImpactoDescendienteResult,
)
from .base_service import BaseCoreService

#: Maximum length of the audited motive (design: motivo 5..500).
MAXIMO_MOTIVO_AUDITADO = 500


@dataclass
class AccionDescendiente:
    """What the correction does with ONE descendant of the link."""

    destino: Encuentro
    slot: str
    bloqueado: bool = False
    motivo_bloqueo: str | None = None
    reemplazar: bool = False
    limpiar_slot: bool = False
    limpiar: bool = False

    @property
    def afecta(self) -> bool:
        """True when the descendant is really modified by the correction."""
        return self.reemplazar or self.limpiar_slot or self.limpiar


class CorreccionCoreService(BaseCoreService):
    """Impact analysis and application of the correction of the winner."""

    # ── reads ──────────────────────────────────────────────────────────────

    def cadena_de(
        self,
        encuentro: Encuentro,
        por_id: dict | None = None,
    ) -> list[tuple[Encuentro, str]]:
        """Descendants reached through the links of the bracket.

        The chain is `(destino, slot)` pairs: the slot is the one the
        predecessor fills. `por_id` allows the flow to reuse the rows it
        already locked.
        """
        cadena: list[tuple[Encuentro, str]] = []
        visitados = {encuentro.id}
        actual = encuentro
        while actual.siguiente_encuentro_id:
            siguiente_id = actual.siguiente_encuentro_id
            if siguiente_id in visitados:
                # A cycle can never be built (the link points forward), but
                # the traversal never loops forever anyway.
                break
            visitados.add(siguiente_id)
            siguiente = por_id.get(siguiente_id) if por_id else None
            if siguiente is None:
                siguiente = actual.siguiente_encuentro
            if siguiente is None:
                break
            cadena.append((siguiente, actual.slot_destino))
            actual = siguiente
        return cadena

    def previsualizar(
        self,
        encuentro: Encuentro,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """Return the impact of the correction. It never writes."""
        ganador_nuevo = self.participante_del_slot(encuentro, ganador_nuevo_id)
        acciones = self._plan(encuentro, ganador_nuevo, self.cadena_de(encuentro))
        return CorreccionPreviewResult(
            encuentro_id=str(encuentro.id),
            ganador_actual_id=(
                str(encuentro.ganador_id) if encuentro.ganador_id else None
            ),
            ganador_nuevo_id=str(ganador_nuevo.id),
            requiere_override=any(accion.bloqueado for accion in acciones),
            descendientes=[self._impacto(accion) for accion in acciones],
        )

    # ── commands ───────────────────────────────────────────────────────────

    def corregir(
        self,
        encuentro: Encuentro,
        ganador_nuevo_id,
        actor=None,
        motivo: str | None = None,
        override: bool = False,
        acepta_impacto: bool = False,
        expected_version: int | None = None,
        por_id: dict | None = None,
    ) -> CorreccionResult:
        """Correct the winner and cascade the change over the descendants."""
        ganador_nuevo = self.participante_del_slot(encuentro, ganador_nuevo_id)

        # Idempotency first: an exact replay writes nothing at all.
        if encuentro.ganador_id == ganador_nuevo.id:
            return self._resultado(
                encuentro,
                [],
                ganador_nuevo,
                False,
                False,
            )

        acciones = self._plan(encuentro, ganador_nuevo, self.cadena_de(encuentro, por_id))

        # A blocked descendant stops the whole correction: without an
        # explicit override NOTHING changes (never a silent cascade).
        bloqueados = [accion for accion in acciones if accion.bloqueado]
        if bloqueados and not (override and acepta_impacto):
            raise DestinoBloqueadoError()

        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)
        motivo_auditoria = self._motivo_auditoria(motivo, override and bloqueados)

        # 1. The corrected encounter keeps its new authoritative winner; the
        #    scores of the previous outcome are cleaned because they would
        #    contradict it.
        encuentro.ganador = ganador_nuevo
        self._limpiar_marcador(encuentro)

        # 2. The cascade over the descendants of the link.
        for accion in acciones:
            self._aplicar_accion(accion, ganador_nuevo, actor, motivo_auditoria)

        self.persistir_cambio(encuentro, actor, motivo_auditoria)

        return self._resultado(
            encuentro,
            acciones,
            ganador_nuevo,
            bool(bloqueados),
            True,
        )

    # ── plan ───────────────────────────────────────────────────────────────

    def _plan(
        self,
        encuentro: Encuentro,
        ganador_nuevo,
        cadena: list[tuple[Encuentro, str]],
    ) -> list[AccionDescendiente]:
        """Compute what the correction does with every descendant.

        The chain carries the value that was propagated. The correction
        replaces that value with the new winner and cleans the results that
        were derived from it. When a descendant had already played with that
        value its own result is void, so ITS advance is void too and the
        slot it filled is emptied instead of being replaced.
        """
        valor_corregido_id = (
            str(encuentro.ganador_id) if encuentro.ganador_id else None
        )
        acciones: list[AccionDescendiente] = []
        vacio = False

        for destino, slot in cadena:
            if CAMPOS_DE_SLOT.get(slot or "") is None:
                continue
            bloqueado, motivo_bloqueo = self._bloqueo(destino)
            accion = AccionDescendiente(
                destino=destino,
                slot=slot,
                bloqueado=bloqueado,
                motivo_bloqueo=motivo_bloqueo,
            )
            acciones.append(accion)

            portador_id = destino.ganador_propagado_id
            ocupante = getattr(destino, CAMPOS_DE_SLOT[slot])
            if portador_id is None or ocupante is None:
                # Nothing was propagated into this slot.
                continue
            if ocupante.id != portador_id:
                # The slot was overwritten by hand after the propagation: the
                # correction never touches a manual placement.
                continue
            if str(portador_id) != valor_corregido_id:
                # Another value flows here (the winner of the descendant):
                # this correction does not affect it.
                continue

            if vacio:
                # The value that flowed here is void: the slot is emptied
                # and the derived result is cleaned.
                accion.limpiar_slot = True
                accion.limpiar = destino.ganador_id == portador_id
                continue

            accion.reemplazar = True
            accion.limpiar = destino.ganador_id == portador_id
            if accion.limpiar:
                # The descendant had already played with the corrected
                # value: its own advance is void too.
                vacio = True

        return acciones

    # ── application ────────────────────────────────────────────────────────

    def _aplicar_accion(
        self,
        accion: AccionDescendiente,
        ganador_nuevo,
        actor,
        motivo: str,
    ) -> None:
        """Apply ONE action of the plan over its descendant."""
        destino = accion.destino
        campo = CAMPOS_DE_SLOT[accion.slot]

        if accion.limpiar_slot:
            setattr(destino, campo, None)
            destino.ganador_propagado = None
        elif accion.reemplazar:
            setattr(destino, campo, ganador_nuevo)
            destino.ganador_propagado = ganador_nuevo

        if accion.limpiar:
            self._anular_resultado(destino)

        if accion.afecta:
            self.persistir_cambio(destino, actor, motivo)

    @staticmethod
    def _limpiar_marcador(encuentro: Encuentro) -> None:
        """Drop the scores of an outcome that no longer holds."""
        encuentro.puntaje_1 = None
        encuentro.puntaje_2 = None
        encuentro.marcador_detalle = ""

    @classmethod
    def _anular_resultado(cls, encuentro: Encuentro) -> None:
        """Void the result derived from a corrected value.

        The encounter becomes replayable but it KEEPS the trace of its
        start: the history is never erased.
        """
        cls._limpiar_marcador(encuentro)
        encuentro.ganador = None
        encuentro.finalizado_en = None
        if encuentro.estado == EstadoEncuentroChoices.FINALIZADO:
            encuentro.estado = EstadoEncuentroChoices.EN_CURSO

    @staticmethod
    def _bloqueo(destino: Encuentro) -> tuple[bool, str | None]:
        """A descendant that started, finished or was cancelled is blocked."""
        if destino.estado in (
            EstadoEncuentroChoices.FINALIZADO,
            EstadoEncuentroChoices.CANCELADO,
        ):
            return True, "El encuentro ya finalizó o fue cancelado."
        if destino.iniciado_en is not None:
            return True, "El encuentro ya había comenzado."
        return False, None

    @staticmethod
    def _motivo_auditoria(motivo: str, con_override: bool) -> str:
        """The audited motive marks explicitly the overridden corrections."""
        if not con_override:
            return motivo
        auditado = f"{motivo} (con override)".strip()
        return auditado[:MAXIMO_MOTIVO_AUDITADO]

    # ── results ────────────────────────────────────────────────────────────

    @staticmethod
    def _impacto(accion: AccionDescendiente) -> ImpactoDescendienteResult:
        """Public shape of the impact over one descendant."""
        destino = accion.destino
        ocupante = getattr(destino, CAMPOS_DE_SLOT[accion.slot])
        return ImpactoDescendienteResult(
            encuentro_id=str(destino.id),
            slot=accion.slot,
            estado=destino.estado,
            ocupante_actual_id=str(ocupante.id) if ocupante is not None else None,
            ganador_propagado_id=(
                str(destino.ganador_propagado_id)
                if destino.ganador_propagado_id
                else None
            ),
            bloqueado=accion.bloqueado,
            motivo_bloqueo=accion.motivo_bloqueo,
            se_reemplaza=accion.reemplazar,
            se_limpia_resultado=accion.limpiar,
        )

    def _resultado(
        self,
        encuentro: Encuentro,
        acciones: list[AccionDescendiente],
        ganador_nuevo,
        requirio_override: bool,
        aplicado: bool,
    ) -> CorreccionResult:
        """Build the result of the correction."""
        return CorreccionResult(
            encuentro_id=str(encuentro.id),
            ganador_id=str(ganador_nuevo.id),
            requirio_override=requirio_override,
            descendientes_afectados=(
                sum(1 for accion in acciones if accion.afecta) if aplicado else 0
            ),
            encuentro=EncuentroResult.desde(encuentro),
            descendientes=[self._impacto(accion) for accion in acciones],
        )
