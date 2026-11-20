"""`AdminController` — la superficie HTTP transversal de la administración.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Ledger: `RT-ADM-01` (GET `/administracion/resumen`) ·
        `RT-ADM-02` (GET `/administracion/auditoria`).

Las dos rutas son NUEVAS y las declara este paquete: el ledger provisional
`SH-05` no tenía una fila para el resumen transversal ni para el acta. Se
pide su ratificación a A0 (`A0-XCT02-03`).

**401 ANTES QUE 403**: las rutas declaran `auth=JWTAuth()` y la capacidad
`admin.ver`. Un anónimo recibe 401 antes de que la capacidad se compruebe
(`core/permissions.py`).

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al orquestador
y devuelve el éxito formateado por el presenter. Los errores los traduce el
catálogo global de `core/exceptions.py`.
"""

from typing import Optional

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.permissions import RequireAdminVer
from core.responses import ApiResponse, success_response
from modules.administracion.domain.services.orchestrators.admin_auditoria_orchestrator import (
    AdminAuditoriaOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_resumen_orchestrator import (
    AdminResumenOrchestrator,
)
from modules.administracion.presentation.presenters.admin_auditoria_presenter import (
    AdminAuditoriaPresenter,
)
from modules.administracion.presentation.presenters.admin_resumen_presenter import (
    AdminResumenPresenter,
)
from modules.administracion.presentation.schemas.admin_auditoria_schemas import (
    AuditoriaListadoOut,
)
from modules.administracion.presentation.schemas.admin_resumen_schemas import (
    ResumenOperativoOut,
)


@api_controller("/administracion", tags=["Administración"])
class AdminController:
    """El resumen operativo y el acta de auditoría del panel."""

    @inject
    def __init__(
        self,
        resumen_orchestrator: AdminResumenOrchestrator,
        auditoria_orchestrator: AdminAuditoriaOrchestrator,
    ):
        self.resumen_orchestrator = resumen_orchestrator
        self.auditoria_orchestrator = auditoria_orchestrator

    @route.get(
        "/resumen",
        response={200: ApiResponse[ResumenOperativoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El estado operativo de la edición.",
    )
    async def resumen(
        self,
        request,
        edicion_id: Optional[str] = Query(
            None,
            description="Edición del resumen. Sin valor, se resuelve la edición publicada única.",
        ),
    ):
        """Route: GET /api/administracion/resumen

        `RT-ADM-01`. Es una LECTURA: el resumen no escribe nada. Las cifras y
        las incidencias las calcula el backend; el navegador no recalcula
        ninguna.
        """
        resultado = await self.resumen_orchestrator.obtener_resumen(edicion_id)

        return success_response(AdminResumenPresenter.present(resultado))

    @route.get(
        "/auditoria",
        response={200: ApiResponse[AuditoriaListadoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
        summary="El acta de las acciones sensibles.",
    )
    async def auditoria(
        self,
        request,
        edicion_id: Optional[str] = Query(None, description="Edición del acta."),
        accion: Optional[str] = Query(None, description="Código de la acción."),
        page: int = Query(1, ge=1, description="Página, 1-based."),
        page_size: int = Query(20, ge=1, le=100, description="Tamaño de la página."),
    ):
        """Route: GET /api/administracion/auditoria

        `RT-ADM-02`. El acta nombra QUIÉN, CUÁNDO, QUÉ y POR QUÉ. No expone
        secretos ni el contexto crudo: el servicio saneó el contexto al
        escribir.
        """
        resultado = await self.auditoria_orchestrator.listar_auditoria(
            edicion_id=edicion_id,
            accion=accion,
            page=page,
            page_size=page_size,
        )

        return success_response(AdminAuditoriaPresenter.present_listado(resultado))


__all__ = ["AdminController"]
