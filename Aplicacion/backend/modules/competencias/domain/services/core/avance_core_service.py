"""El AVANCE del ganador: vista previa y confirmación.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

`RN-K02` y `QA-K04`: "Advance preview no escribe; confirm sí".

**La vista previa NO ESCRITE NADA.** Es una simulación: dice a dónde
llegaría el ganador, qué slot ocupa hoy ese destino y si la cascada está
BLOQUEADA. La confirmación es la única que escribe, y lo hace con su motivo
auditado.

**Un destino que YA transcurrió BLOQUEA la cascada** (`DESTINO_BLOQUEADO`):
un destino `FINALIZADO`, `CANCELADO` o ya iniciado no puede reescribirse en
silencio (`frontend/05` §6: "corrección descendente no puede ser silenciosa").

**El ganador propagado se registra APARTE** (`ganador_propagado`): así una
corrección posterior distingue una colocación PROPAGADA de una colocada a
mano, y nunca pisa una colocación manual.
"""

from modules.competencias.domain.constants import (
    CAMPOS_DE_SLOT,
    EstadoEncuentro,
)
from modules.competencias.domain.exceptions import (
    DestinoBloqueadoError,
    EnlaceInvalidoError,
    GanadorInvalidoError,
    SlotOcupadoError,
)
from modules.competencias.domain.models import Encuentro
from modules.competencias.domain.results.competencias_results import (
    AvancePreviewResult,
    AvanceResult,
)
from modules.competencias.domain.services.core.base_service import BaseCoreService


class AvanceCoreService(BaseCoreService):
    """Propuesta y aplicación de la propagación del ganador."""

    # ── lecturas ───────────────────────────────────────────────────────────

    def destino_de(self, encuentro: Encuentro) -> Encuentro:
        """El encuentro enlazado, o el error de enlace (422)."""
        if not encuentro.siguiente_encuentro_id or not encuentro.slot_destino:
            raise EnlaceInvalidoError()
        return encuentro.siguiente_encuentro

    def previsualizar(self, encuentro: Encuentro) -> AvancePreviewResult:
        """La PROPUESTA de la propagación. NO escribe nada.

        Es la operación que `QA-K04` exige: la previa informa del efecto
        exacto antes de que el administrador confirme.
        """
        destino = self.destino_de(encuentro)
        ganador = self._ganador(encuentro)
        ocupante = self._ocupante(destino, encuentro.slot_destino)
        bloqueado, motivo_bloqueo = self._bloqueo(destino)
        ya_propagado = self._ya_propagado(destino, encuentro.slot_destino, ganador)
        equipo = getattr(ganador, "equipo", None)
        return AvancePreviewResult(
            encuentro_id=str(encuentro.id),
            siguiente_encuentro_id=str(destino.id),
            slot_destino=encuentro.slot_destino,
            ganador_equipo_id=str(ganador.equipo_id),
            ganador_equipo_nombre=equipo.nombre if equipo is not None else "",
            ocupante_actual_equipo_id=(
                str(ocupante.equipo_id) if ocupante is not None else None
            ),
            ya_propagado=ya_propagado,
            bloqueado=bloqueado,
            motivo_bloqueo=motivo_bloqueo,
            puede_confirmar=(
                not bloqueado
                and not ya_propagado
                and (ocupante is None or str(ocupante.id) == str(ganador.id))
            ),
        )

    # ── comandos ───────────────────────────────────────────────────────────

    def confirmar(
        self,
        encuentro: Encuentro,
        destino: Encuentro,
        *,
        expected_version: int | None,
        motivo: str | None,
    ) -> AvanceResult:
        """Coloca al ganador en el slot de destino y registra la propagación."""
        ganador = self._ganador(encuentro)
        ocupante = self._ocupante(destino, encuentro.slot_destino)

        # Idempotencia primero: un reintento exacto no escribe nada.
        if self._ya_propagado(destino, encuentro.slot_destino, ganador):
            return self._resultado(encuentro, destino, ganador, ya_aplicado=True)

        bloqueado, _ = self._bloqueo(destino)
        if bloqueado:
            raise DestinoBloqueadoError()
        if ocupante is not None and str(ocupante.id) != str(ganador.id):
            raise SlotOcupadoError()

        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)

        campo = CAMPOS_DE_SLOT[encuentro.slot_destino]
        setattr(destino, campo, ganador)
        destino.ganador_propagado = ganador
        self.persistir_cambio(destino, motivo)

        return self._resultado(encuentro, destino, ganador, ya_aplicado=False)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _ganador(encuentro: Encuentro):
        """El ganador del encuentro: es obligatorio para avanzar."""
        if encuentro.ganador_id is None:
            raise GanadorInvalidoError()
        return encuentro.ganador

    @staticmethod
    def _ocupante(destino: Encuentro, slot_destino: str):
        """El equipo que ocupa hoy el slot de destino."""
        campo = CAMPOS_DE_SLOT.get(slot_destino or "")
        if campo is None:
            raise EnlaceInvalidoError()
        return getattr(destino, campo)

    @staticmethod
    def _bloqueo(destino: Encuentro) -> tuple[bool, str | None]:
        """Un destino que empezó, finalizó o fue cancelado está BLOQUEADO."""
        if destino.estado in (
            EstadoEncuentro.FINALIZADO,
            EstadoEncuentro.CANCELADO,
        ):
            return True, "El encuentro de destino ya finalizó o fue cancelado."
        if destino.iniciado_en is not None:
            return True, "El encuentro de destino ya había comenzado."
        return False, None

    @staticmethod
    def _ya_propagado(destino: Encuentro, slot_destino: str, ganador) -> bool:
        """Si la propagación ya está aplicada (reintento exacto)."""
        campo = CAMPOS_DE_SLOT.get(slot_destino or "")
        if campo is None:
            return False
        ocupante = getattr(destino, campo)
        if ocupante is None or str(ocupante.id) != str(ganador.id):
            return False
        return str(destino.ganador_propagado_id or "") == str(ganador.id)

    @staticmethod
    def _resultado(
        encuentro: Encuentro,
        destino: Encuentro,
        ganador,
        *,
        ya_aplicado: bool,
    ) -> AvanceResult:
        """El resultado del avance."""
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        equipo = getattr(ganador, "equipo", None)
        return AvanceResult(
            encuentro_origen_id=str(encuentro.id),
            siguiente_encuentro_id=str(destino.id),
            slot_destino=encuentro.slot_destino,
            ganador_equipo_id=str(ganador.equipo_id),
            ganador_equipo_nombre=equipo.nombre if equipo is not None else "",
            ya_aplicado=ya_aplicado,
            destino=proyectar_encuentro(destino),
        )


__all__ = ["AvanceCoreService"]
