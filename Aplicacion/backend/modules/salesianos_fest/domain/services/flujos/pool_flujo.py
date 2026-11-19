"""`PoolFlujo` — el pool de cupos de una inscripción: agregar, mover y retirar.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC,
ABREN `transaction.atomic()`.

Este flujo implementa `FL-05` ("Gestionar plantilla") y las reglas congeladas
que lo acompañan:

**RN-I03 — El saldo disponible nunca es negativo.** El saldo lo calcula el
servidor como `cupos_pagados - cupos_asignados`, y el contador se mueve con
un `UPDATE` ATÓMICO CONDICIONAL (`CapacidadCoreService.reservar_cupo`). Dos
asignaciones simultáneas NO pueden sobre-suscribir el pool (`QA-I05`).

**RN-I04 — Retirar libera el cupo, no el dinero.** Retirar una participación
la pasa a `RETIRADA` y devuelve SU cupo al pool de ESA inscripción. No anula
la compra, no devuelve dinero y no aumenta el inventario de un evento
(`DEC-06`).

**RN-I05 — La elegibilidad se verifica SIEMPRE en backend.** Ninguna regla
de elegibilidad, tope ni solapamiento se resuelve en el cliente:

| Regla | Comprobación |
|---|---|
| edition | el equipo pertenece a la inscripción |
| disciplina activa | `Disciplina.estado = ACTIVA` |
| disciplina permitida | la disciplina está en el paquete de la inscripción |
| compatibilidad | la modalidad de la disciplina admite el género declarado |
| tope | el equipo no alcanzó `Disciplina.maximo_por_equipo` |
| duplicado | la persona no participa ya en esta inscripción |
| solapamiento | la persona no participa en la misma disciplina de la edición |

**RN-I06 — Ampliar no duplica beneficios.** Este flujo NO concede beneficios:
sólo lo hace la ACTIVACIÓN de derechos, y sólo en el alta.

**MOVIMIENTO (`FL-05` paso 4).** `reemplaza_participacion_id` retira una
participación y asigna su cupo a la persona nueva DENTRO de la misma
transacción: el saldo disponible nunca baja de cero por un movimiento.
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.salesianos_fest.domain.constants import (
    CausaOperativaPool,
    EstadoDisciplina,
    EstadoParticipacion,
    ModalidadDisciplina,
    RolParticipante,
)
from modules.salesianos_fest.domain.exceptions import (
    DisciplinaNoPermitidaError,
    EquipoCompletoError,
    EquipoNoEncontradoError,
    InscripcionNoEncontradaError,
    ParticipanteDuplicadoError,
    ParticipanteNoElegibleError,
    ParticipanteNoEncontradoError,
    PersonaNoEncontradaError,
    SinCuposDisponiblesError,
)
from modules.salesianos_fest.domain.ports import IResolucionPersonaService
from modules.salesianos_fest.domain.results.pool_result import (
    ImpedimentoResult,
    ParticipacionResult,
    PoolResult,
)
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.selectors.pool_selector import PoolSelector
from modules.salesianos_fest.domain.services.core.catalogo_core_service import (
    CatalogoCoreService,
)
from modules.salesianos_fest.domain.services.core.capacidad_core_service import (
    CapacidadCoreService,
)
from modules.salesianos_fest.domain.services.core.pool_core_service import (
    PoolCoreService,
)

#: Códigos de los impedimentos que publica el pool.
IMPOS_SIN_CUPOS = "SIN_CUPOS_DISPONIBLES"
IMPOS_EQUIPO_COMPLETO = "EQUIPO_COMPLETO"

#: Mensajes públicos de los impedimentos. Son prosa FIJA: no interpolan
#: identificadores, nombres ni cifras.
MENSAJE_SIN_CUPOS = "No hay cupos pagados disponibles en esta inscripción."
MENSAJE_EQUIPO_COMPLETO = "El equipo alcanzó el máximo de participantes permitido."


class PoolFlujo:
    """Casos de uso de escritura y lectura del pool de una inscripción."""

    @inject
    def __init__(
        self,
        pool_selector: PoolSelector,
        pool_core: PoolCoreService,
        capacidad_core: CapacidadCoreService,
        inscripcion_selector: InscripcionSelector,
        catalogo_core: CatalogoCoreService,
        resolucion_persona: IResolucionPersonaService,
    ):
        self.pool_selector = pool_selector
        self.pool_core = pool_core
        self.capacidad_core = capacidad_core
        self.inscripcion_selector = inscripcion_selector
        self.catalogo_core = catalogo_core
        self.resolucion_persona = resolucion_persona

    # ── Lectura ─────────────────────────────────────────────────────────────

    async def obtener_pool(self, inscripcion_id) -> PoolResult:
        """El estado del pool de una inscripción.

        Returns:
            El pool con la aritmética de cupos y los impedimentos.
        """
        inscripcion = await sync_to_async(self._obtener_inscripcion)(inscripcion_id)
        return await sync_to_async(self._construir_pool)(
            inscripcion,
            CausaOperativaPool.PARTICIPACION_AGREGADA,
        )

    # ── Escritura ───────────────────────────────────────────────────────────

    async def agregar_participante(
        self,
        data: ParticipanteAsignarData,
    ) -> PoolResult:
        """Agrega un participante al pool, o MUEVE su cupo a otro.

        Returns:
            El pool después de la operación.
        """
        inscripcion = await sync_to_async(self._obtener_inscripcion)(
            data.inscripcion_id
        )
        persona = await sync_to_async(self._obtener_persona)(data)
        equipo = await sync_to_async(self._obtener_equipo)(
            inscripcion,
            data.equipo_id,
        )
        await sync_to_async(self._validar_elegibilidad)(inscripcion, equipo, persona)
        await sync_to_async(self._validar_rol)(data.rol)

        causa = (
            CausaOperativaPool.CUPO_REASIGNADO
            if data.reemplaza_participacion_id
            else CausaOperativaPool.PARTICIPACION_AGREGADA
        )
        await sync_to_async(self._agregar_sync)(
            inscripcion,
            persona,
            equipo,
            data.rol,
            data.reemplaza_participacion_id,
        )
        inscripcion = await sync_to_async(self._obtener_inscripcion)(inscripcion.id)
        return await sync_to_async(self._construir_pool)(inscripcion, causa)

    async def retirar_participante(
        self,
        inscripcion_id,
        participacion_id,
    ) -> PoolResult:
        """Retira un participante: libera su cupo y no toca la compra.

        Returns:
            El pool después de la retirada.
        """
        inscripcion = await sync_to_async(self._obtener_inscripcion)(inscripcion_id)
        await sync_to_async(self._retirar_sync)(inscripcion, participacion_id)
        inscripcion = await sync_to_async(self._obtener_inscripcion)(inscripcion_id)
        return await sync_to_async(self._construir_pool)(
            inscripcion,
            CausaOperativaPool.PARTICIPACION_RETIRADA,
        )

    # ── Internos sync ───────────────────────────────────────────────────────

    def _obtener_inscripcion(self, inscripcion_id):
        """La inscripción, o `INSCRIPCION_NO_ENCONTRADA`."""
        inscripcion = self.inscripcion_selector.obtener_por_id(inscripcion_id)
        if inscripcion is None:
            raise InscripcionNoEncontradaError()
        return inscripcion

    def _obtener_persona(self, data: ParticipanteAsignarData):
        """La persona del padrón, por identificador o por documento."""
        if data.persona_id is not None:
            persona = self.resolucion_persona.resolver_por_id(data.persona_id)
        else:
            persona = self.resolucion_persona.resolver_por_documento(
                data.tipo_documento,
                data.numero_documento,
            )
        if persona is None:
            raise PersonaNoEncontradaError()
        return persona

    def _obtener_equipo(self, inscripcion, equipo_id):
        """El equipo DENTRO de la inscripción, o `EQUIPO_NO_ENCONTRADO`."""
        equipo = self.inscripcion_selector.obtener_equipo(
            inscripcion.id,
            equipo_id,
        )
        if equipo is None:
            raise EquipoNoEncontradoError()
        return equipo

    def _validar_rol(self, rol: str) -> None:
        """El rol pertenece al vocabulario cerrado."""
        if rol not in RolParticipante.values:
            raise ParticipanteNoElegibleError()

    def _validar_elegibilidad(self, inscripcion, equipo, persona) -> None:
        """Las reglas de elegibilidad del servidor (`RN-I05`)."""
        disciplina = equipo.disciplina

        if disciplina.estado != EstadoDisciplina.ACTIVA:
            raise ParticipanteNoElegibleError()

        # `disciplina_permitida` exige que la disciplina sea de la EDICIÓN
        # del paquete, esté activa y esté vinculada al paquete: con ella, la
        # comprobación de edición y de paquete es una sola.
        if self.catalogo_core.disciplina_permitida(
            inscripcion.paquete,
            disciplina.id,
        ) is None:
            raise DisciplinaNoPermitidaError()

        if not self._genero_compatible(persona, disciplina):
            raise ParticipanteNoElegibleError()

        activos = self.pool_selector.contar_activas_por_equipo(equipo.id)
        if activos >= disciplina.maximo_por_equipo:
            raise EquipoCompletoError()

    @staticmethod
    def _genero_compatible(persona, disciplina) -> bool:
        """Si el género declarado por la persona admite la disciplina.

        Una disciplina `MIXTO` admite cualquier persona. Una disciplina
        `FEMENINO` o `MASCULINO` exige un género DECLARADO: sin género
        conocido no se puede afirmar la compatibilidad, así que no se
        concede el beneficio de la duda.
        """
        modalidad = disciplina.modalidad
        if modalidad == ModalidadDisciplina.MIXTO:
            return True
        genero = (persona.genero or "").strip().upper()
        if not genero:
            return False
        if modalidad == ModalidadDisciplina.FEMENINO:
            return genero == "F"
        if modalidad == ModalidadDisciplina.MASCULINO:
            return genero == "M"
        return False

    @transaction.atomic()
    def _agregar_sync(
        self,
        inscripcion,
        persona,
        equipo,
        rol: str,
        reemplaza_participacion_id,
    ) -> None:
        """La asignación del cupo, atómica.

        El orden importa: primero se libera el cupo de la participación que
        se reemplaza (si la hay) y después se reserva el nuevo. Así un
        movimiento NUNCA falla por falta de saldo disponible.
        """
        if reemplaza_participacion_id is not None:
            self._retirar_participacion_sync(
                inscripcion,
                reemplaza_participacion_id,
                motivo="Cupo reasignado a otro participante.",
            )

        self._verificar_duplicados(inscripcion, equipo, persona)

        if not self.capacidad_core.reservar_cupo(inscripcion.id):
            raise SinCuposDisponiblesError()

        self.pool_core.crear_participacion(
            inscripcion=inscripcion,
            persona=persona,
            equipo=equipo,
            rol=rol,
        )

    def _verificar_duplicados(self, inscripcion, equipo, persona) -> None:
        """La persona no participa ya aquí ni se solapa en la misma disciplina."""
        activa = self.pool_selector.obtener_participacion_activa(
            inscripcion.id,
            persona.id,
        )
        if activa is not None:
            raise ParticipanteDuplicadoError()

        solapada = self.pool_selector.obtener_participacion_activa_en_disciplina(
            inscripcion.edicion_id,
            equipo.disciplina_id,
            persona.id,
        )
        if solapada is not None:
            raise ParticipanteNoElegibleError()

    @transaction.atomic()
    def _retirar_sync(self, inscripcion, participacion_id) -> None:
        """La retirada, atómica."""
        self._retirar_participacion_sync(inscripcion, participacion_id)

    def _retirar_participacion_sync(
        self,
        inscripcion,
        participacion_id,
        *,
        motivo: str = "",
    ) -> None:
        """Retira la participación indicada y libera su cupo.

        No toca la compra, ni la orden de pago, ni el historial comercial:
        retirar es un hecho de la PLANTILLA (`RN-I04`).
        """
        participacion = self.pool_selector.obtener_participacion(participacion_id)
        if (
            participacion is None
            or participacion.inscripcion_id != inscripcion.id
            or participacion.estado != EstadoParticipacion.ACTIVA
        ):
            raise ParticipanteNoEncontradoError()

        self.pool_core.retirar_participacion(participacion, motivo=motivo)
        self.capacidad_core.liberar_cupo(inscripcion.id)

    # ── Proyección ──────────────────────────────────────────────────────────

    def _construir_pool(self, inscripcion, causa_operativa: str) -> PoolResult:
        """Proyecta la inscripción con su pool, su saldo y sus impedimentos."""
        participaciones = list(self.pool_selector.listar_participaciones(inscripcion.id))
        disponibles = max(
            inscripcion.cupos_pagados - inscripcion.cupos_asignados,
            0,
        )
        return PoolResult(
            inscripcion_id=str(inscripcion.id),
            responsable_id=str(inscripcion.responsable_id),
            cupos_pagados=inscripcion.cupos_pagados,
            cupos_asignados=inscripcion.cupos_asignados,
            cupos_disponibles=disponibles,
            participaciones=[
                self._presentar_participacion(participacion)
                for participacion in participaciones
            ],
            impedimentos=self._impedimentos(inscripcion, disponibles),
            causa_operativa=causa_operativa,
        )

    def _impedimentos(self, inscripcion, disponibles: int) -> list[ImpedimentoResult]:
        """Las causas concretas que impiden ampliar la plantilla.

        `FL-05` paso 5: "el administrador ve causas concretas de equipo
        incompleto/no elegible".
        """
        impedimentos: list[ImpedimentoResult] = []
        if disponibles <= 0:
            impedimentos.append(
                ImpedimentoResult(
                    codigo=IMPOS_SIN_CUPOS,
                    mensaje=MENSAJE_SIN_CUPOS,
                )
            )
        for equipo in self.inscripcion_selector.listar_equipos(inscripcion.id):
            disciplina = equipo.disciplina
            activos = self.pool_selector.contar_activas_por_equipo(equipo.id)
            if activos >= disciplina.maximo_por_equipo:
                impedimentos.append(
                    ImpedimentoResult(
                        codigo=IMPOS_EQUIPO_COMPLETO,
                        mensaje=MENSAJE_EQUIPO_COMPLETO,
                        equipo_id=str(equipo.id),
                    )
                )
        return impedimentos

    @staticmethod
    def _presentar_participacion(participacion) -> ParticipacionResult:
        """Proyecta una participación del pool."""
        return ParticipacionResult(
            id=str(participacion.id),
            persona_id=str(participacion.persona_id),
            persona_nombres=participacion.persona.nombres,
            persona_apellidos=participacion.persona.apellidos,
            equipo_id=str(participacion.equipo_id),
            equipo_nombre=participacion.equipo.nombre,
            disciplina_id=str(participacion.disciplina_id),
            disciplina_nombre=participacion.disciplina.nombre,
            rol=participacion.rol,
            estado=participacion.estado,
            ocupa_cupo=participacion.estado == EstadoParticipacion.ACTIVA,
            retirada_en=participacion.retirada_en,
        )


__all__ = [
    "IMPOS_EQUIPO_COMPLETO",
    "IMPOS_SIN_CUPOS",
    "MENSAJE_EQUIPO_COMPLETO",
    "MENSAJE_SIN_CUPOS",
    "PoolFlujo",
]
