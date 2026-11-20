"""`EncuentroFlujo` — la EDICIÓN de un encuentro del cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

Un SOLO comando de edición (`EncuentroActualizarData`) con campos opcionales:
un campo AUSENTE significa "no tocar"; un campo presente se aplica.

El orden de aplicación es FIJO y no depende del orden del JSON:

1. **participantes** — para que la comprobación de solapamiento use los
   participantes NUEVOS;
2. **horario** — con el intervalo válido, la regla de no solapamiento
   (`RN-K03`) y la promoción `BORRADOR → PROGRAMADO`;
3. **enlace** — destino y slot viajan juntos;
4. **bye** — el bye manual exige EXACTAMENTE un equipo;
5. **estado** — la transición por el ciclo de vida.

**El bloqueo optimista se toma UNA vez**, al principio del comando: si el
cliente viaja una versión obsoleta, el comando se rechaza con
`RESOURCE_CHANGED` y NO se escribe nada (`frontend/05` §5).Tomar el bloqueo
por grupo escribiría dos veces con la misma versión esperada y la segunda
fallaría sola.

**Cada grupo que cambia algo deja su ACTA**: el historial explica qué se
movió, por qué y quién lo movió (`RN-K02`).
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import (
    HorarioInvalidoError,
    SolapamientoHorarioError,
)
from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.results.competencias_results import (
    EncuentroResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroActualizarData,
)
from modules.competencias.domain.selectors.encuentro_selector import (
    EncuentroSelector,
)
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.encuentro_core_service import (
    EncuentroCoreService,
)
from modules.competencias.domain.services.core.programacion_core_service import (
    ProgramacionCoreService,
)


class EncuentroFlujo:
    """Casos de uso de edición de un encuentro del cuadro."""

    @inject
    def __init__(
        self,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
        auditoria_core: AuditoriaCoreService,
        selector: EncuentroSelector,
    ):
        self.encuentro_core = encuentro_core
        self.programacion_core = programacion_core
        self.auditoria_core = auditoria_core
        self.selector = selector

    async def actualizar_encuentro(
        self,
        competencia_id,
        encuentro_id,
        data: EncuentroActualizarData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> EncuentroResult:
        """Aplica los cambios declarados en el comando de edición."""
        encuentro = await sync_to_async(self._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self._actualizar_sync)(
            encuentro,
            data,
            expected_version,
            actor,
        )

    # ── internos ───────────────────────────────────────────────────────────

    def _obtener_encuentro(self, competencia_id, encuentro_id):
        """El encuentro, comprobando que es de la competencia indicada."""
        from modules.competencias.domain.exceptions import EncuentroNoEncontradoError
        from modules.competencias.domain.models import Encuentro

        encuentro = (
            Encuentro.objects.select_related(
                "ronda",
                "ronda__competencia",
                "participante_1",
                "participante_1__equipo",
                "participante_2",
                "participante_2__equipo",
                "ganador",
                "ganador__equipo",
                "siguiente_encuentro",
                "siguiente_encuentro__siguiente_encuentro",
            )
            .filter(id=encuentro_id, ronda__competencia_id=competencia_id)
            .first()
        )
        if encuentro is None:
            raise EncuentroNoEncontradoError()
        return encuentro

    @transaction.atomic()
    def _actualizar_sync(self, encuentro, data, expected_version, actor):
        """Aplicación atómica de los grupos tocados por el comando."""
        tocados = set(data.model_fields_set) - {"motivo"}
        if not tocados:
            return self._proyectar(encuentro)

        if not self._hay_cambios(encuentro, data, tocados):
            # Reintento idempotente: el estado persistido YA es el pedido.
            return self._proyectar(encuentro)

        # El bloqueo optimista se toma UNA vez para todo el comando.
        self.encuentro_core.aplicar_cas(encuentro, expected_version)

        if {"participante_1_id", "participante_2_id"} & tocados:
            self._aplicar_participantes(encuentro, data, tocados, actor)
        if {"inicio_programado", "fin_programado"} & tocados:
            self._aplicar_horario(encuentro, data, tocados, actor)
        if {"siguiente_encuentro_id", "slot_destino"} & tocados:
            self._aplicar_enlace(encuentro, data, tocados, actor)
        if "es_bye" in tocados:
            self._aplicar_bye(encuentro, data, actor)
        if "estado" in tocados:
            self._aplicar_estado(encuentro, data, actor)

        return self._proyectar(encuentro)

    # ── grupos ─────────────────────────────────────────────────────────────

    def _aplicar_participantes(self, encuentro, data, tocados, actor):
        """Mueve los equipos de los slots declarados."""
        participante_1 = self._valor_del_slot(
            encuentro,
            data,
            tocados,
            "participante_1_id",
            "participante_1_id",
        )
        participante_2 = self._valor_del_slot(
            encuentro,
            data,
            tocados,
            "participante_2_id",
            "participante_2_id",
        )
        antes = (
            str(encuentro.participante_1_id or ""),
            str(encuentro.participante_2_id or ""),
        )
        self.encuentro_core.asignar_participantes(
            encuentro,
            participante_1_id=participante_1,
            participante_2_id=participante_2,
            expected_version=None,
            motivo=data.motivo,
        )
        despues = (
            str(encuentro.participante_1_id or ""),
            str(encuentro.participante_2_id or ""),
        )
        if antes == despues:
            return
        self.auditoria_core.registrar(
            accion=AccionAuditada.PARTICIPANTES,
            motivo=data.motivo or "Cambio de participantes",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={"antes": list(antes), "despues": list(despues)},
        )

    def _aplicar_horario(self, encuentro, data, tocados, actor):
        """Fija, retira o rechaza el horario del encuentro."""
        inicio = (
            data.inicio_programado
            if "inicio_programado" in tocados
            else encuentro.inicio_programado
        )
        fin = (
            data.fin_programado if "fin_programado" in tocados else encuentro.fin_programado
        )
        if (inicio is None) != (fin is None):
            raise HorarioInvalidoError()

        if inicio is None:
            if (
                encuentro.inicio_programado is None
                and encuentro.fin_programado is None
            ):
                # Ya estaba sin horario: no hay nada que retirar ni escribir.
                return
            # Desprogramar: el horario se retira y el encuentro vuelve a
            # `BORRADOR` si estaba `PROGRAMADO`.
            antes = (encuentro.inicio_programado, encuentro.fin_programado)
            encuentro.inicio_programado = None
            encuentro.fin_programado = None
            if encuentro.estado == EstadoEncuentro.PROGRAMADO:
                encuentro.estado = EstadoEncuentro.BORRADOR
            self.encuentro_core.persistir_cambio(encuentro, data.motivo)
            self.auditoria_core.registrar(
                accion=AccionAuditada.PROGRAMACION,
                motivo=data.motivo or "Retiro de la programación",
                competencia=encuentro.ronda.competencia,
                encuentro=encuentro,
                actor=actor,
                detalle={"antes": [str(antes[0]), str(antes[1])]},
            )
            return

        competencia = encuentro.ronda.competencia
        self.programacion_core.validar_horario(competencia, inicio, fin)
        solapes = self.programacion_core.detectar_solape(
            self.programacion_core.equipos_de_encuentro(encuentro),
            inicio,
            fin,
            excluir_encuentro_id=encuentro.id,
        )
        if solapes:
            # El equipo ya juega en esa franja: la agenda NO cambia.
            raise SolapamientoHorarioError()

        antes = (encuentro.inicio_programado, encuentro.fin_programado)
        encuentro.inicio_programado = inicio
        encuentro.fin_programado = fin
        if encuentro.estado == EstadoEncuentro.BORRADOR:
            encuentro.estado = EstadoEncuentro.PROGRAMADO
        self.encuentro_core.persistir_cambio(encuentro, data.motivo)
        self.auditoria_core.registrar(
            accion=AccionAuditada.PROGRAMACION,
            motivo=data.motivo or "Programación del encuentro",
            competencia=competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={
                "antes": [str(antes[0]), str(antes[1])],
                "despues": [str(inicio), str(fin)],
            },
        )

    def _aplicar_enlace(self, encuentro, data, tocados, actor):
        """Enlaza o desenlaza el encuentro con su destino."""
        siguiente = (
            data.siguiente_encuentro_id
            if "siguiente_encuentro_id" in tocados
            else (
                str(encuentro.siguiente_encuentro_id)
                if encuentro.siguiente_encuentro_id
                else None
            )
        )
        slot = (
            data.slot_destino
            if "slot_destino" in tocados
            else encuentro.slot_destino
        )
        antes = (str(encuentro.siguiente_encuentro_id or ""), encuentro.slot_destino or "")
        self.encuentro_core.enlazar(
            encuentro,
            siguiente_encuentro_id=siguiente,
            slot_destino=slot,
            expected_version=None,
            motivo=data.motivo,
        )
        despues = (str(encuentro.siguiente_encuentro_id or ""), encuentro.slot_destino or "")
        if antes == despues:
            return
        self.auditoria_core.registrar(
            accion=AccionAuditada.ENLACE,
            motivo=data.motivo or "Cambio de enlace",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={"antes": list(antes), "despues": list(despues)},
        )

    def _aplicar_bye(self, encuentro, data, actor):
        """Configura el bye manual: exige EXACTAMENTE un equipo."""
        if not data.es_bye:
            # Quitar el bye de un encuentro que ya lo es no es posible: un
            # bye resuelto es terminal.
            if encuentro.es_bye:
                from modules.competencias.domain.exceptions import (
                    TransicionInvalidaError,
                )

                raise TransicionInvalidaError()
            return
        antes = bool(encuentro.es_bye)
        self.encuentro_core.configurar_bye(
            encuentro,
            expected_version=None,
            motivo=data.motivo,
        )
        if antes == bool(encuentro.es_bye):
            return
        self.auditoria_core.registrar(
            accion=AccionAuditada.BYE,
            motivo=data.motivo or "Asignación de bye manual",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={"es_bye": True},
        )

    def _aplicar_estado(self, encuentro, data, actor):
        """Mueve el encuentro por su ciclo de vida."""
        antes = encuentro.estado
        self.encuentro_core.cambiar_estado(
            encuentro,
            data.estado,
            expected_version=None,
            motivo=data.motivo,
        )
        if antes == encuentro.estado:
            return
        accion = (
            AccionAuditada.CANCELACION
            if encuentro.estado == EstadoEncuentro.CANCELADO
            else AccionAuditada.ESTADO
        )
        self.auditoria_core.registrar(
            accion=accion,
            motivo=data.motivo or "Cambio de estado del encuentro",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={"antes": antes, "despues": encuentro.estado},
        )

    # ── utilidades ─────────────────────────────────────────────────────────

    @staticmethod
    def _valor_del_slot(encuentro, data, tocados, campo, atributo):
        """El valor final de un slot: el declarado o el que ya tenía."""
        if campo in tocados:
            return data.participante_1_id if campo == "participante_1_id" else data.participante_2_id
        actual = getattr(encuentro, atributo)
        return str(actual) if actual is not None else None

    @staticmethod
    def _hay_cambios(encuentro, data, tocados) -> bool:
        """Si el comando pediría realmente un cambio."""
        if {"participante_1_id", "participante_2_id"} & tocados:
            if not (
                EncuentroFlujo._slot_igual(
                    encuentro,
                    data,
                    tocados,
                    "participante_1_id",
                    "participante_1_id",
                )
                and EncuentroFlujo._slot_igual(
                    encuentro,
                    data,
                    tocados,
                    "participante_2_id",
                    "participante_2_id",
                )
            ):
                return True
        if {"inicio_programado", "fin_programado"} & tocados:
            inicio = (
                data.inicio_programado
                if "inicio_programado" in tocados
                else encuentro.inicio_programado
            )
            fin = (
                data.fin_programado
                if "fin_programado" in tocados
                else encuentro.fin_programado
            )
            if inicio != encuentro.inicio_programado or fin != encuentro.fin_programado:
                return True
        if {"siguiente_encuentro_id", "slot_destino"} & tocados:
            siguiente = (
                data.siguiente_encuentro_id
                if "siguiente_encuentro_id" in tocados
                else (
                    str(encuentro.siguiente_encuentro_id)
                    if encuentro.siguiente_encuentro_id
                    else None
                )
            )
            slot = (
                data.slot_destino
                if "slot_destino" in tocados
                else encuentro.slot_destino
            )
            if str(siguiente or "") != str(encuentro.siguiente_encuentro_id or ""):
                return True
            if (slot or "") != (encuentro.slot_destino or ""):
                return True
        if "es_bye" in tocados and bool(data.es_bye) != bool(encuentro.es_bye):
            return True
        if "estado" in tocados and data.estado != encuentro.estado:
            return True
        return False

    @staticmethod
    def _slot_igual(encuentro, data, tocados, campo, atributo) -> bool:
        """Si el slot declarado ya es el que hay."""
        if campo not in tocados:
            return True
        declarado = (
            data.participante_1_id if campo == "participante_1_id" else data.participante_2_id
        )
        actual = getattr(encuentro, atributo)
        return str(declarado or "") == str(actual or "")

    @staticmethod
    def _proyectar(encuentro) -> EncuentroResult:
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        return proyectar_encuentro(encuentro)


__all__ = ["EncuentroFlujo"]
