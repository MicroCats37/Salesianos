"""`AdminInscripcionController` — la superficie HTTP de las inscripciones.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

| Ruta | Método | Ledger | Wrapper |
|---|---|---|---|
| `/administracion/inscripciones` | GET | `RT-IN-07` | `PaginatedData[AdminInscripcionListItemOut]` |
| `/administracion/inscripciones/{inscripcion_id}` | GET | `RT-IN-08` | `AdminInscripcionDetalleOut` |
| `/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}` | DELETE | `A0-UI04-04` | `PoolOut` |

**401 ANTES QUE 403**: las rutas declaran `auth=JWTAuth()` y la capacidad
`admin.ver`. Un anónimo recibe 401 antes de que la capacidad se compruebe
(`core/permissions.py`).

El controller es "SAGRADO": cero lógica. Sólo parsea, delega al orquestador
y devuelve el éxito formateado por el presenter. Los errores los traduce el
catálogo global de `core/exceptions.py`.
"""

from typing import Optional

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.exceptions import NotFoundError
from core.pagination import PaginatedData
from core.permissions import RequireAdminVer, RequireInscripcionesEscribir
from core.responses import ApiResponse, paginated_response, success_response
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.presentation.presenters.admin_operacion_presenter import (
    AdminOperacionPresenter,
)
from modules.administracion.presentation.schemas.admin_operacion_schemas import (
    AdminInscripcionDetalleOut,
    AdminInscripcionListItemOut,
    PoolOut,
    RetirarParticipanteIn,
)


@api_controller("/administracion", tags=["Administración"])
class AdminInscripcionController:
    """Las inscripciones del panel de administración."""

    @inject
    def __init__(self, orchestrator: AdminOperacionOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "/inscripciones",
        response={200: ApiResponse[PaginatedData[AdminInscripcionListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="La lista administrativa de las inscripciones.",
    )
    async def listar_inscripciones(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None, description="Edición del listado. Sin valor, la edición publicada."
        ),
        q: Optional[str] = Query(None, description="Búsqueda sobre responsable o paquete."),
        ordering: Optional[str] = Query(
            None, description="Orden (lista blanca): created_at, estado, responsable, paquete."
        ),
        estado_pago: Optional[str] = Query(
            None, description="Filtro del saldo comercial: PENDIENTE o PAGADO."
        ),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/inscripciones

        `RT-IN-07`. Es una LECTURA. `estado_pago` es el filtro que el
        resumen declara para su drilldown: la lista devuelve exactamente
        las inscripciones con cupos sin pagar.
        """
        items, total, pagina, tamano, paginas = (
            await self.orchestrator.listar_inscripciones(
                edicion_id=edicion_id,
                q=q or "",
                ordering=ordering or "",
                estado_pago=estado_pago or "",
                page=page,
                page_size=page_size,
            )
        )

        return paginated_response(
            items=[AdminOperacionPresenter.present_inscripcion_lista(item) for item in items],
            total=total,
            page=pagina,
            page_size=tamano,
        )

    @route.get(
        "/inscripciones/{inscripcion_id}",
        response={200: ApiResponse[AdminInscripcionDetalleOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El detalle administrativo de una inscripción.",
    )
    async def obtener_inscripcion(self, request, inscripcion_id: str):
        """Route: GET /api/administracion/inscripciones/{inscripcion_id}

        `RT-IN-08`. El POOL y sus IMPEDIMENTOS son los que publica el
        dueño (`PoolFlujo`): este módulo no los reconstruye.
        """
        detalle = await self.orchestrator.obtener_inscripcion(inscripcion_id)

        if detalle is None:
            raise NotFoundError(resource="Inscripción", code="RESOURCE_NOT_FOUND")

        return success_response(
            AdminOperacionPresenter.present_inscripcion_detalle(detalle)
        )

    @route.delete(
        "/inscripciones/{inscripcion_id}/participantes/{participacion_id}",
        response={200: ApiResponse[PoolOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer, RequireInscripcionesEscribir],
        summary="La retirada administrativa de un participante.",
    )
    async def retirar_participante(
        self,
        request,
        inscripcion_id: str,
        participacion_id: str,
        payload: RetirarParticipanteIn,
    ):
        """Route: DELETE /api/administracion/inscripciones/{id}/participantes/{id}

        **COMANDO SENSIBLE.** El motivo es OBLIGATORIO (422
        `MOTIVO_REQUERIDO` si falta) y la acción queda en el ACTA
        transversal con QUIÉN, CUÁNDO, QUÉ y POR QUÉ.

        El efecto lo aplica el módulo DUEÑO: la retirada libera el cupo de
        ESA inscripción y no toca la compra, ni la orden de pago, ni el
        historial comercial (`RN-I04` · `DEC-06`).

        La respuesta es el pool ACTUALIZADO.
        """
        pool = await self.orchestrator.retirar_participante(
            actor=request.auth,
            inscripcion_id=inscripcion_id,
            participacion_id=participacion_id,
            motivo=payload.motivo,
            version=payload.version,
        )

        return success_response(
            AdminOperacionPresenter.present_pool(pool),
            message="La participación se retiró correctamente.",
        )


__all__ = ["AdminInscripcionController"]
