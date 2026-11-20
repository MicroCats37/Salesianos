"""`AdminOperacionOrchestrator` — la fachada async de la CAPA OPERATIVA.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Fachada async y EXTREMADAMENTE delgada: un método público por endpoint y
sólo delegación (`contract/django-app-architecture-contract.md` §4.5).

## El alcance de la EDICIÓN

Las lecturas del panel son de UNA edición. El alcance lo decide el ORDEN
CONGELADO de resolución (`FREEZE-ED-1.0.0` · `FR-02` §2.2) a través del
servicio del módulo `eventos`. **No hay un fallback silencioso**: si la
edición no se puede resolver, la respuesta es el error del catálogo.

La búsqueda de personas (`RT-ID-07`) NO es de una edición: es una búsqueda
global, y la edición sólo acota las participaciones que se publican.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)
from modules.administracion.domain.services.flujos.admin_accion_sensible_flujo import (
    AdminAccionSensibleFlujo,
)
from modules.pagos.domain.services.flujos.aprobar_pago_manual_flujo import (
    AprobarPagoManualFlujo,
)
from modules.eventos.domain.services.core.edicion_scope_service import (
    EdicionScopeService,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo


class AdminOperacionOrchestrator:
    """Fachada async de las superficies operativas del panel."""

    @inject
    def __init__(
        self,
        servicio: AdminOperacionService,
        accion_flujo: AdminAccionSensibleFlujo,
        scope: EdicionScopeService,
        pool_flujo: PoolFlujo,
        aprobar_pago_manual_flujo: AprobarPagoManualFlujo,
    ):
        self.servicio = servicio
        self.accion_flujo = accion_flujo
        self.scope = scope
        self.pool_flujo = pool_flujo
        self.aprobar_pago_manual_flujo = aprobar_pago_manual_flujo

    # ── Inscripciones (RT-IN-07 · RT-IN-08) ──────────────────────────────────

    async def listar_inscripciones(
        self,
        edicion_id=None,
        q: str = "",
        ordering: str = "",
        estado_pago: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las inscripciones de la edición resuelta, paginadas."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)

        return await sync_to_async(self.servicio.listar_inscripciones)(
            edicion.id,
            q=q,
            ordering=ordering,
            estado_pago=estado_pago,
            page=page,
            page_size=page_size,
        )

    async def obtener_inscripcion(self, inscripcion_id):
        """El detalle de una inscripción, con el pool que publica el dueño.

        El POOL no se reconstruye aquí: es el `PoolResult` de `PoolFlujo`,
        con sus impedimentos y sus causas.
        """
        pool = await self.pool_flujo.obtener_pool(inscripcion_id)

        return await sync_to_async(self.servicio.obtener_inscripcion)(
            inscripcion_id, pool=pool
        )

    # ── Equipos (RT-IN-09 · RT-IN-10) ────────────────────────────────────────

    async def listar_equipos(
        self,
        edicion_id=None,
        q: str = "",
        ordering: str = "",
        plantilla: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Los equipos de la edición resuelta, paginados."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)

        return await sync_to_async(self.servicio.listar_equipos)(
            edicion.id,
            q=q,
            ordering=ordering,
            plantilla=plantilla,
            page=page,
            page_size=page_size,
        )

    async def obtener_equipo(self, equipo_id):
        """El detalle de un equipo."""
        return await sync_to_async(self.servicio.obtener_equipo)(equipo_id)

    # ── Participantes (RT-IN-11) ─────────────────────────────────────────────

    async def listar_participantes(
        self,
        edicion_id=None,
        q: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las personas que participan en la edición resuelta, paginadas."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)

        return await sync_to_async(self.servicio.listar_participantes)(
            edicion.id,
            q=q,
            page=page,
            page_size=page_size,
        )

    # ── Pagos (RT-PG-04 · RT-PG-07) ──────────────────────────────────────────

    async def listar_pagos(
        self,
        edicion_id=None,
        q: str = "",
        ordering: str = "",
        estado_operativo: str = "",
        estado_compra: str = "",
        estado_orden: str = "",
        tipo: str = "",
        desde=None,
        hasta=None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Los pagos de la edición resuelta, paginados."""
        edicion = await sync_to_async(self._resolver_edicion)(edicion_id)

        return await sync_to_async(self.servicio.listar_pagos)(
            edicion.id,
            q=q,
            ordering=ordering,
            estado_operativo=estado_operativo,
            estado_compra=estado_compra,
            estado_orden=estado_orden,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
            page=page,
            page_size=page_size,
        )

    async def obtener_pago(self, compra_id):
        """El detalle comercial de un pago."""
        return await sync_to_async(self.servicio.obtener_pago)(compra_id)

    async def aprobar_pago_manual(
        self, *, orden_pago_id: str, actor_id: str, canal: str, referencia: str, motivo: str
    ):
        """Registra evidencia manual y devuelve la fila de pago actualizada."""
        await self.aprobar_pago_manual_flujo.aprobar(
            orden_pago_id=orden_pago_id,
            actor_id=actor_id,
            canal=canal,
            referencia=referencia,
            motivo=motivo,
        )
        return await sync_to_async(self.servicio.obtener_pago_por_orden)(orden_pago_id)

    # ── Personas (RT-ID-07 · RT-ID-08) ───────────────────────────────────────

    async def listar_personas(
        self,
        q: str = "",
        edicion_id=None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las personas del sistema, paginadas.

        La búsqueda es GLOBAL: no hay edición que resolver. Si el cliente
        manda `edicion_id`, esa edición acota las participaciones que se
        publican; el conjunto de personas no se acota.
        """
        if edicion_id:
            edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
            edicion_id = str(edicion.id)

        return await sync_to_async(self.servicio.listar_personas)(
            q=q,
            edicion_id=edicion_id,
            page=page,
            page_size=page_size,
        )

    async def obtener_persona(self, persona_id, edicion_id=None):
        """El detalle de una persona."""
        if edicion_id:
            edicion = await sync_to_async(self._resolver_edicion)(edicion_id)
            edicion_id = str(edicion.id)

        return await sync_to_async(self.servicio.obtener_persona)(
            persona_id, edicion_id=edicion_id
        )

    # ── Comandos sensibles ───────────────────────────────────────────────────

    async def retirar_participante(
        self,
        actor,
        inscripcion_id,
        participacion_id,
        motivo: str,
        version: str | None = None,
    ):
        """La retirada administrativa de un participante.

        El efecto lo aplica el DUEÑO; el motivo, la versión y el acta son
        de esta capa. La respuesta es el pool ACTUALIZADO, ya proyectado a
        la forma del panel.
        """
        pool = await self.accion_flujo.retirar_participante(
            actor=actor,
            inscripcion_id=inscripcion_id,
            participacion_id=participacion_id,
            motivo=motivo,
            version=version,
        )

        return await sync_to_async(self.servicio.proyectar_pool)(pool)

    # ── Internos ─────────────────────────────────────────────────────────────

    def _resolver_edicion(self, edicion_id):
        """La edición del alcance, con el orden congelado de `FR-02`."""
        if edicion_id:
            return self.scope.resolver_explicita(edicion_id)

        return self.scope.resolver_actual(permitir_publicada_por_defecto=True)


__all__ = ["AdminOperacionOrchestrator"]
