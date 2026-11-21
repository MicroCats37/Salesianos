"""`PaseController` — superficie HTTP de los pases, beneficiarios y cortesías.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-RT-1.0.0` ·
        `FREEZE-ED-1.0.0`

Ledger: `RT-PS-01`…`RT-PS-08` (provisionales, `SH-05` §1.4) ·
        `RT-CM-02` (CONGELADO, `FR-07` §3.3) ·
        `RT-RT-03` (CONGELADO, `FR-07` §3.3).

| Ruta | Método | Presenter | Wrapper |
|---|---|---|---|
| `RT-PS-01` | GET `/pases` | `PaseCatalogoPresenter` | `PaseCatalogoOut` |
| `RT-PS-02` | GET `/pases/{pase_id}` | `PaseDetallePresenter` | `PaseDetalleOut` |
| `RT-CM-02` | POST `/pases/compras` | `CompraPasePresenter` | `CompraPaseCreadaOut` |
| `RT-PS-03` | GET `/pases/compras/{compra_pase_id}` | `PaseCompraDetallePresenter` | `PaseCompraDetalleOut` |
| `RT-PS-04` | GET `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiariosPresenter` | `PaseBeneficiariosOut` |
| `RT-PS-05` | POST `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiarioAsignarPresenter` | `PaseBeneficiariosOut` |
| `RT-RT-03` | DELETE `/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}` | `PaseBeneficiarioPresenter` | `PaseBeneficiarioRevocadoOut` |
| `RT-PS-06` | GET `/administracion/pases` | `AdminPaseListaPresenter` | `PaginatedData[AdminPaseListItemOut]` |
| `RT-PS-07` | GET `/administracion/pases/cortesias` | `AdminCortesiaListaPresenter` | `PaginatedData[AdminCortesiaListItemOut]` |
| `RT-PS-08` | POST `/administracion/pases/cortesias` | `AdminCortesiaCrearPresenter` | `AdminCortesiaOut` |
| `RT-PS-09` | POST `/administracion/pases/cortesias/{cortesia_id}/revocar` | `AdminCortesiaRevocarPresenter` | `AdminCortesiaRevocadaOut` |

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.

**LA CREDENCIAL DEL ENLACE.** Las rutas de gestión de una compra aceptan el
token privado en la cabecera `X-Pase-Token`. El token es de ÁMBITO POR COMPRA:
abre ESA compra y ninguna otra. El DNI **nunca** es una credencial
(`RN-U04`): sin token y sin cuenta, la respuesta es 401.

**EL ADMINISTRADOR.** Las rutas `/administracion/...` declaran la puerta
compartida `RequireAdmin`, que responde **401** a un anónimo antes que 403
(`core/permissions.py`).
"""

from uuid import UUID

from asgiref.sync import sync_to_async
from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from ninja_jwt.authentication import JWTAuth

from core.pagination import PaginatedData
from core.permissions import RequireAdmin
from core.responses import ApiResponse, paginated_response, success_response
from modules.salesianos_fest.domain.constants import CABECERA_TOKEN_PASE
from modules.salesianos_fest.domain.schemas.pase_schemas import (
    AsignarBeneficiarioData,
    ComprarPaseData,
    OtorgarCortesiaData,
    RevocarBeneficiarioData,
    RevocarCortesiaData,
)
from modules.salesianos_fest.domain.services.orchestrators.beneficiario_orchestrator import (
    BeneficiarioOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.cortesia_orchestrator import (
    CortesiaOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.pase_orchestrator import (
    PaseOrchestrator,
)
from modules.salesianos_fest.presentation.presenters.admin_pase_presenter import (
    AdminCortesiaCrearPresenter,
    AdminCortesiaListaPresenter,
    AdminCortesiaRevocarPresenter,
    AdminPaseListaPresenter,
)
from modules.salesianos_fest.presentation.presenters.beneficiario_presenter import (
    PaseBeneficiarioAsignarPresenter,
    PaseBeneficiarioPresenter,
    PaseBeneficiariosPresenter,
    PaseCompraDetallePresenter,
)
from modules.salesianos_fest.presentation.presenters.compra_pase_presenter import (
    CompraPasePresenter,
)
from modules.salesianos_fest.presentation.presenters.pase_presenter import (
    PaseCatalogoPresenter,
    PaseDetallePresenter,
)
from modules.salesianos_fest.presentation.schemas.pase_schemas import (
    AdminCortesiaListItemOut,
    AdminCortesiaOut,
    AdminCortesiaRevocadaOut,
    AdminPaseListItemOut,
    AsignarBeneficiarioIn,
    CompraPaseCreadaOut,
    ComprarPaseIn,
    OtorgarCortesiaIn,
    PaseBeneficiarioRevocadoOut,
    PaseBeneficiariosOut,
    PaseCompraDetalleOut,
    PaseCatalogoOut,
    PaseDetalleOut,
    RevocarCortesiaIn,
)


@api_controller("/pases", tags=["Pases"])
class PaseController:
    """Catálogo, compra y gestión de pases."""

    @inject
    def __init__(
        self,
        orchestrator: PaseOrchestrator,
        beneficiario_orchestrator: BeneficiarioOrchestrator,
    ):
        self.orchestrator = orchestrator
        self.beneficiario_orchestrator = beneficiario_orchestrator

    # ── Catálogo ────────────────────────────────────────────────────────────

    @route.get(
        "",
        response={200: ApiResponse[PaseCatalogoOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Pases comprables de la edición del alcance.",
    )
    async def listar_pases(
        self,
        request,
        edicion_id: UUID = Query(
            None,
            description=(
                "Edición del alcance. Si se omite, se resuelve por el orden "
                "congelado de edición."
            ),
        ),
    ):
        """Route: GET /api/pases

        El catálogo es REAL y está acotado por EDICIÓN (`RN-E01`). Un pase
        sin precio vigente NO aparece: no hay precio de reserva.
        """
        result = await self.orchestrator.listar_pases(edicion_id)
        return success_response(
            PaseCatalogoPresenter.present_catalogo(result),
            message="Catálogo de pases consultado correctamente.",
        )

    # ── Compra ──────────────────────────────────────────────────────────────

    @route.post(
        "/compras",
        response={201: ApiResponse[CompraPaseCreadaOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Compra un lote de pases, con cuenta o como invitado.",
    )
    async def comprar_pase(self, request, payload: ComprarPaseIn):
        """Route: POST /api/pases/compras

        `RT-CM-02`. La compra puede ser INVITADA: no hace falta cuenta y
        **no se crea ninguna** (`FL-06` paso 2). El comprador es el actor si
        la petición va autenticada, y la identidad civil declarada si no.

        El precio NO lo declara el cliente: lo resuelve el servidor contra
        el catálogo vigente (`RN-C02`). El lote queda `PENDIENTE` y no
        habilita ningún pase hasta que el pago se active (`RN-P02`).
        """
        data = ComprarPaseData(
            pase_id=str(payload.pase_id),
            cantidad=payload.cantidad,
            tipo_documento=payload.tipo_documento,
            numero_documento=payload.numero_documento,
            nombres=payload.nombres,
            apellidos=payload.apellidos,
            contacto_email=payload.contacto_email,
        )
        result = await self.orchestrator.comprar_pase(
            await _actor_opcional(request),
            data,
        )
        return success_response(
            CompraPasePresenter.present_compra(result),
            message="Compra de pases registrada correctamente.",
        )

    @route.get(
        "/{pase_id}",
        response={200: ApiResponse[PaseDetalleOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Detalle de un pase del catálogo.",
    )
    async def obtener_pase(
        self,
        request,
        pase_id: UUID,
        edicion_id: UUID = Query(
            None,
            description="Edición del alcance del pase.",
        ),
    ):
        """Route: GET /api/pases/{pase_id}

        El precio puede venir vacío: un pase sin precio vigente NO tiene
        precio de reserva inventado.
        """
        result = await self.orchestrator.obtener_pase(edicion_id, pase_id)
        return success_response(
            PaseDetallePresenter.present_detalle(result),
            message="Pase consultado correctamente.",
        )

    # ── Gestión del lote ────────────────────────────────────────────────────

    @route.get(
        "/compras/{compra_pase_id}",
        response={200: ApiResponse[PaseCompraDetalleOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Detalle de la compra de un lote de pases.",
    )
    async def obtener_compra(self, request, compra_pase_id: UUID):
        """Route: GET /api/pases/compras/{compra_pase_id}

        Abre el lote el TITULAR autenticado, un ADMINISTRADOR o el portador
        del TOKEN de gestión. Sin credencial válida la respuesta es 401.
        """
        token = self._token_de_la_peticion(request)
        result = await self.orchestrator.obtener_compra(
            await _actor_opcional(request),
            compra_pase_id,
            token,
        )
        return success_response(
            PaseCompraDetallePresenter.present_detalle(result),
            message="Compra de pases consultada correctamente.",
        )

    @route.get(
        "/compras/{compra_pase_id}/beneficiarios",
        response={200: ApiResponse[PaseBeneficiariosOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Derechos otorgados en un lote de pases.",
    )
    async def listar_beneficiarios(self, request, compra_pase_id: UUID):
        """Route: GET /api/pases/compras/{compra_pase_id}/beneficiarios"""
        token = self._token_de_la_peticion(request)
        result = await self.orchestrator.listar_beneficiarios(
            await _actor_opcional(request),
            compra_pase_id,
            token,
        )
        return success_response(
            PaseBeneficiariosPresenter.present_beneficiarios(result),
            message="Beneficiarios de la compra consultados correctamente.",
        )

    @route.post(
        "/compras/{compra_pase_id}/beneficiarios",
        response={200: ApiResponse[PaseBeneficiariosOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Asigna un pase comprado a una persona.",
    )
    async def asignar_beneficiario(
        self,
        request,
        compra_pase_id: UUID,
        payload: AsignarBeneficiarioIn,
    ):
        """Route: POST /api/pases/compras/{compra_pase_id}/beneficiarios

        `RT-PS-05`. Sólo se asigna capacidad PAGADA: un lote pendiente no
        tiene pases que repartir (`RN-P02`). Un derecho NO se duplica: la
        misma persona no puede tener dos derechos activos del mismo pase
        (`RN-P07`).
        """
        data = AsignarBeneficiarioData(
            persona_id=str(payload.persona_id) if payload.persona_id else None,
            tipo_documento=payload.tipo_documento,
            numero_documento=payload.numero_documento,
            nombres=payload.nombres,
            apellidos=payload.apellidos,
            motivo=payload.motivo,
        )
        token = self._token_de_la_peticion(request)
        result = await self.beneficiario_orchestrator.asignar_beneficiario(
            await _actor_opcional(request),
            compra_pase_id,
            data,
            token,
        )
        return success_response(
            PaseBeneficiarioAsignarPresenter.present_asignacion(result),
            message="Pase asignado correctamente.",
        )

    @route.delete(
        "/compras/{compra_pase_id}/beneficiarios/{persona_id}",
        response={200: ApiResponse[PaseBeneficiarioRevocadoOut]},
        auth=None,
        permissions=[AllowAny],
        summary="Revoca el derecho de entrada de una persona.",
    )
    async def revocar_beneficiario(
        self,
        request,
        compra_pase_id: UUID,
        persona_id: UUID,
        motivo: str = Query(
            "",
            max_length=500,
            description="Motivo de la revocación. Se conserva en la auditoría.",
        ),
    ):
        """Route: DELETE /api/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}

        `RT-RT-03`. La revocación es PERMANENTE, AUDITADA e IDEMPOTENTE
        (`FR-05` §2.3). No devuelve la unidad al lote: la política de
        reasignación sigue ABIERTA (`PD-02`).

        El ledger congelado declara esta ruta SIN schema de entrada: el
        motivo viaja como parámetro de consulta.
        """
        data = RevocarBeneficiarioData(motivo=motivo or "")
        token = self._token_de_la_peticion(request)
        result = await self.beneficiario_orchestrator.revocar_beneficiario(
            await _actor_opcional(request),
            compra_pase_id,
            persona_id,
            data,
            token,
        )
        return success_response(
            PaseBeneficiarioPresenter.present_revocacion(result),
            message="Pase revocado correctamente.",
        )

    # ── Internos ────────────────────────────────────────────────────────────

    @staticmethod
    def _token_de_la_peticion(request) -> str | None:
        """El token privado de gestión que viaja en la cabecera.

        PARSEAR la cabecera es trabajo del controller: el dominio recibe el
        token como un dato y decide. La cabecera puede no existir.
        """
        headers = getattr(request, "headers", None) or {}
        valor = headers.get(CABECERA_TOKEN_PASE) or headers.get(
            CABECERA_TOKEN_PASE.lower()
        )
        if not valor:
            return None
        return str(valor).strip() or None


@api_controller("/administracion/pases", tags=["Administración de pases"])
class AdminPaseController:
    """Administración de lotes de pases y cortesías."""

    @inject
    def __init__(
        self,
        orchestrator: PaseOrchestrator,
        cortesia_orchestrator: CortesiaOrchestrator,
    ):
        self.orchestrator = orchestrator
        self.cortesia_orchestrator = cortesia_orchestrator

    @route.get(
        "",
        response={200: ApiResponse[PaginatedData[AdminPaseListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Listado de lotes de pases.",
    )
    async def listar_pases(
        self,
        request,
        edicion_id: UUID = Query(None, description="Edición del alcance."),
        estado: str = Query(None, description="Estado de la compra."),
        page: int = Query(1, ge=1, description="Página (1-based)."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de página."),
    ):
        """Route: GET /api/administracion/pases

        `RT-PS-06`. El listado NUNCA expone el token de gestión: es una
        credencial y un listado es un sitio donde se filtra.
        """
        result = await self.orchestrator.listar_compras(
            edicion_id,
            estado,
            page,
            page_size,
        )
        return paginated_response(
            AdminPaseListaPresenter.present_lista(result).items,
            result.total,
            result.page,
            result.page_size,
            message="Lotes de pases consultados correctamente.",
        )

    @route.get(
        "/cortesias",
        response={200: ApiResponse[PaginatedData[AdminCortesiaListItemOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Listado de cortesías otorgadas.",
    )
    async def listar_cortesias(
        self,
        request,
        edicion_id: UUID = Query(None, description="Edición del alcance."),
        estado: str = Query(None, description="Estado de la cortesía."),
        page: int = Query(1, ge=1, description="Página (1-based)."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de página."),
    ):
        """Route: GET /api/administracion/pases/cortesias

        `RT-PS-07`. Cada fila es un ACTA: actor, motivo y fecha.
        """
        result = await self.cortesia_orchestrator.listar_cortesias(
            edicion_id,
            estado,
            page,
            page_size,
        )
        return paginated_response(
            AdminCortesiaListaPresenter.present_lista(result).items,
            result.total,
            result.page,
            result.page_size,
            message="Cortesías consultadas correctamente.",
        )

    @route.post(
        "/cortesias",
        response={201: ApiResponse[AdminCortesiaOut]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Otorga una cortesía con actor y motivo.",
    )
    async def otorgar_cortesia(self, request, payload: OtorgarCortesiaIn):
        """Route: POST /api/administracion/pases/cortesias

        `RT-PS-08`. Registra un derecho GRATUITO con auditoría. **Nunca**
        crea una orden ni una transacción de pago (`FL-07` paso 3,
        `RN-P05`).
        """
        data = OtorgarCortesiaData(
            edicion_id=str(payload.edicion_id),
            pase_id=str(payload.pase_id),
            persona_id=str(payload.persona_id) if payload.persona_id else None,
            tipo_documento=payload.tipo_documento,
            numero_documento=payload.numero_documento,
            nombres=payload.nombres,
            apellidos=payload.apellidos,
            motivo=payload.motivo,
        )
        result = await self.cortesia_orchestrator.otorgar_cortesia(
            request.auth,
            data,
        )
        return success_response(
            AdminCortesiaCrearPresenter.present_cortesia(result),
            message="Cortesía registrada correctamente.",
        )

    @route.post(
        "/cortesias/{cortesia_id}/revocar",
        response={200: ApiResponse[AdminCortesiaRevocadaOut]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Revoca una cortesía con motivo.",
    )
    async def revocar_cortesia(
        self,
        request,
        cortesia_id: UUID,
        payload: RevocarCortesiaIn,
    ):
        """Route: POST /api/administracion/pases/cortesias/{cortesia_id}/revocar

        Revoca el acta y su DERECHO. Es IDEMPOTENTE: repetirla devuelve 200
        con `ya_revocado=true` y el mismo estado final (`FR-05` §2.3).

        **NO TOCA HECHOS FINANCIEROS** (`RN-P05`): la cortesía no los tiene y
        la revocación tampoco los crea. La revocación es PERMANENTE: los
        consumos ya realizados quedan (`RN-P08`).
        """
        data = RevocarCortesiaData(
            cortesia_id=str(cortesia_id),
            motivo=payload.motivo,
        )
        result = await self.cortesia_orchestrator.revocar_cortesia(
            request.auth,
            data,
        )
        return success_response(
            AdminCortesiaRevocarPresenter.present(result),
            message="Cortesía revocada correctamente.",
        )


_AUTENTICACION_OPCIONAL = JWTAuth()


async def _actor_opcional(request):
    """Resuelve un Bearer opcional sin convertir al invitado en error."""
    cabecera = request.headers.get("Authorization") or ""
    partes = cabecera.split(" ")
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return None
    return await sync_to_async(_AUTENTICACION_OPCIONAL.authenticate)(
        request,
        partes[1],
    )


__all__ = ["AdminPaseController", "PaseController"]
