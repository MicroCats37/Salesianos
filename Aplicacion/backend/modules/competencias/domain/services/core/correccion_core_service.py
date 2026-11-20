"""La CORRECCIÓN del resultado: impacto explícito y cascada controlada.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

`RN-K02` y `QA-K03`: "Preview de impacto y confirmación sin cascada oculta".

**La vista previa NO ESCRITE NADA.** Calcula el PLAN de la corrección: qué
le pasa a cada descendiente de la cadena. El administrador lo ve ANTES de
confirmar, y el resultado publica el número de encuentros afectados
(`frontend/05` §3: "La corrección afecta a 2 encuentros posteriores").

**Sin cascada oculta.** Un descendiente que YA transcurrió (finalizado,
cancelado o iniciado) BLOQUEA la corrección: sin un `override` explícito Y la
aceptación del impacto calculado, NO se escribe NADA (`DESTINO_BLOQUEADO`).

**La corrección NUNCA pisa una colocación MANUAL.** Sólo toca los slots
cuyo valor PROPAGÓ (`ganador_propagado`): un slot que el administrador
colocó a mano queda intacto, y su estado se conserva en la historia.

**El motivo es OBLIGATORIO** (`MOTIVO_REQUERIDO`): una corrección es una
decisión administrativa y queda auditada.
"""

from dataclasses import dataclass

from modules.competencias.domain.constants import (
    CAMPOS_DE_SLOT,
    EstadoEncuentro,
)
from modules.competencias.domain.exceptions import (
    DestinoBloqueadoError,
    GanadorInvalidoError,
)
from modules.competencias.domain.models import Encuentro
from modules.competencias.domain.results.competencias_results import (
    CorreccionImpactoResult,
    CorreccionPreviewResult,
    CorreccionResult,
)
from modules.competencias.domain.services.core.base_service import BaseCoreService


@dataclass
class AccionDescendiente:
    """Lo que la corrección le hace a UN descendiente de la cadena."""

    destino: Encuentro
    slot: str
    bloqueado: bool = False
    motivo_bloqueo: str | None = None
    reemplazar: bool = False
    limpiar_slot: bool = False
    limpiar: bool = False

    @property
    def afecta(self) -> bool:
        """Si el descendiente cambia DE VERDAD."""
        return self.reemplazar or self.limpiar_slot or self.limpiar


class CorreccionCoreService(BaseCoreService):
    """Análisis de impacto y aplicación de la corrección del ganador."""

    # ── lecturas ───────────────────────────────────────────────────────────

    def cadena_de(self, encuentro: Encuentro, por_id=None) -> list[tuple]:
        """La cadena de descendientes: (encuentro destino, slot)."""
        if por_id is None:
            por_id = {}
        cadena: list[tuple] = []
        actual = encuentro
        visto: set[str] = {str(encuentro.id)}
        while actual.siguiente_encuentro is not None:
            siguiente = actual.siguiente_encuentro
            clave = str(siguiente.id)
            if clave in visto:
                # Una cadena cíclica no se propaga: se corta.
                break
            visto.add(clave)
            destino = por_id.get(clave, siguiente)
            cadena.append((destino, actual.slot_destino))
            actual = destino
        return cadena

    def previsualizar(
        self,
        encuentro: Encuentro,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """El IMPACTO de la corrección. NO escribe nada."""
        ganador_nuevo = self.participante_del_slot(encuentro, ganador_nuevo_id)
        acciones = self._plan(encuentro, ganador_nuevo, self.cadena_de(encuentro))
        equipo = getattr(ganador_nuevo, "equipo", None)
        return CorreccionPreviewResult(
            encuentro_id=str(encuentro.id),
            ganador_actual_equipo_id=(
                str(encuentro.ganador_id) if encuentro.ganador_id else None
            ),
            ganador_nuevo_equipo_id=str(ganador_nuevo.equipo_id),
            ganador_nuevo_equipo_nombre=equipo.nombre if equipo is not None else "",
            requiere_override=any(accion.bloqueado for accion in acciones),
            total_afectados=sum(1 for accion in acciones if accion.afecta),
            descendientes=[self._impacto(accion) for accion in acciones],
            puede_confirmar=not any(accion.bloqueado for accion in acciones),
        )

    # ── comandos ───────────────────────────────────────────────────────────

    def corregir(
        self,
        encuentro: Encuentro,
        ganador_nuevo_id,
        *,
        expected_version: int | None,
        motivo: str | None,
        override: bool = False,
        acepta_impacto: bool = False,
    ) -> CorreccionResult:
        """Corrige el ganador y propaga el cambio sobre los descendientes."""
        ganador_nuevo = self.participante_del_slot(encuentro, ganador_nuevo_id)

        # Idempotencia primero: un reintento exacto no escribe nada.
        if str(encuentro.ganador_id or "") == str(ganador_nuevo.id):
            return self._resultado(encuentro, [], ganador_nuevo, False, False)

        acciones = self._plan(encuentro, ganador_nuevo, self.cadena_de(encuentro))

        # Un descendiente bloqueado detiene TODA la corrección: sin un
        # override explícito Y la aceptación del impacto, NADA cambia.
        bloqueados = [accion for accion in acciones if accion.bloqueado]
        if bloqueados and not (override and acepta_impacto):
            raise DestinoBloqueadoError()

        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)

        # 1. El encuentro corregido conserva su nuevo ganador autoritativo;
        #    el marcador anterior se limpia porque lo contradiría.
        encuentro.ganador = ganador_nuevo
        self._limpiar_marcador(encuentro)

        # 2. La cascada sobre los descendientes del enlace.
        for accion in acciones:
            self._aplicar_accion(accion, ganador_nuevo, motivo)

        self.persistir_cambio(encuentro, motivo)

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
        cadena: list[tuple],
    ) -> list[AccionDescendiente]:
        """Calcula qué le hace la corrección a cada descendiente.

        La cadena transporta el valor que se propagó. La corrección
        reemplaza ese valor por el ganador nuevo y limpia los resultados que
        se derivaron de él. Cuando un descendiente YA JUGÓ con ese valor, su
        propio resultado queda anulado, así que su avance también: el slot
        que llenó se VACÍA en vez de reemplazarse.
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
                # No se propagó nada a este slot.
                continue
            if str(ocupante.id) != str(portador_id):
                # El slot se sobrescribió A MANO después de la propagación:
                # la corrección NUNCA toca una colocación manual.
                continue
            if str(portador_id) != valor_corregido_id:
                # Por aquí fluye otro valor: esta corrección no le afecta.
                continue

            if vacio:
                # El valor que fluye aquí quedó anulado: se vacía el slot y
                # se limpia el resultado derivado.
                accion.limpiar_slot = True
                accion.limpiar = str(destino.ganador_id or "") == str(portador_id)
                continue

            accion.reemplazar = True
            accion.limpiar = str(destino.ganador_id or "") == str(portador_id)
            if accion.limpiar:
                # El descendiente ya jugó con el valor corregido: su propio
                # avance queda anulado también.
                vacio = True

        return acciones

    # ── aplicación ─────────────────────────────────────────────────────────

    def _aplicar_accion(
        self,
        accion: AccionDescendiente,
        ganador_nuevo,
        motivo: str,
    ) -> None:
        """Aplica el plan sobre UN descendiente."""
        destino = accion.destino
        if accion.reemplazar:
            setattr(destino, CAMPOS_DE_SLOT[accion.slot], ganador_nuevo)
            destino.ganador_propagado = ganador_nuevo
        if accion.limpiar_slot:
            setattr(destino, CAMPOS_DE_SLOT[accion.slot], None)
            destino.ganador_propagado = None
        if accion.limpiar:
            self._anular_resultado(destino)
        if accion.afecta:
            self.persistir_cambio(destino, motivo)

    @staticmethod
    def _limpiar_marcador(encuentro: Encuentro) -> None:
        """Retira el marcador de un resultado que ya no se sostiene."""
        encuentro.puntaje_1 = None
        encuentro.puntaje_2 = None
        encuentro.marcador_detalle = ""

    @classmethod
    def _anular_resultado(cls, encuentro: Encuentro) -> None:
        """Anula el resultado derivado de un valor corregido.

        El encuentro vuelve a ser jugable pero CONSERVA la traza de su
        inicio: la historia nunca se borra.
        """
        cls._limpiar_marcador(encuentro)
        encuentro.ganador = None
        encuentro.finalizado_en = None
        if encuentro.estado == EstadoEncuentro.FINALIZADO:
            encuentro.estado = EstadoEncuentro.EN_CURSO

    @staticmethod
    def _bloqueo(destino: Encuentro) -> tuple[bool, str | None]:
        """Un descendiente que empezó, finalizó o fue cancelado está BLOQUEADO."""
        if destino.estado in (
            EstadoEncuentro.FINALIZADO,
            EstadoEncuentro.CANCELADO,
        ):
            return True, "El encuentro ya finalizó o fue cancelado."
        if destino.iniciado_en is not None:
            return True, "El encuentro ya había comenzado."
        return False, None

    # ── proyección ─────────────────────────────────────────────────────────

    @staticmethod
    def _impacto(accion: AccionDescendiente) -> CorreccionImpactoResult:
        """La proyección del impacto sobre un descendiente."""
        return CorreccionImpactoResult(
            encuentro_id=str(accion.destino.id),
            slot=accion.slot,
            bloqueado=accion.bloqueado,
            motivo_bloqueo=accion.motivo_bloqueo,
            reemplaza=accion.reemplazar,
            limpia_slot=accion.limpiar_slot,
            limpia_resultado=accion.limpiar,
            afecta=accion.afecta,
        )

    @staticmethod
    def _resultado(
        encuentro: Encuentro,
        acciones: list[AccionDescendiente],
        ganador_nuevo,
        override_aplicado: bool,
        escrito: bool,
    ) -> CorreccionResult:
        """El resultado de la corrección."""
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        equipo = getattr(ganador_nuevo, "equipo", None)
        return CorreccionResult(
            encuentro_id=str(encuentro.id),
            ganador_nuevo_equipo_id=str(ganador_nuevo.equipo_id),
            ganador_nuevo_equipo_nombre=equipo.nombre if equipo is not None else "",
            descendientes_afectados=(
                sum(1 for accion in acciones if accion.afecta) if escrito else 0
            ),
            override_aplicado=override_aplicado,
            encuentro=proyectar_encuentro(encuentro),
            descendientes=[
                CorreccionCoreService._impacto(accion) for accion in acciones
            ],
        )


__all__ = ["AccionDescendiente", "CorreccionCoreService"]
