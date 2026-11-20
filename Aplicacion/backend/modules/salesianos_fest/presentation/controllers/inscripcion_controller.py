"""`InscripcionController` — superficie HTTP de las inscripciones.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-ID-1.0.0`
Ledger: `SH-05` §1.3 (`RT-IN-02`, `RT-IN-04`) y `RT-IN-14` (**nuevo,
PROVISIONAL**: el alta de la inscripción inicial no tenía fila en el ledger
y se pide su ratificación a A0).

Packet `DOM-02` (2026-11-19) añade cuatro rutas CONGELADAS:

| Ruta | Método | Presenter | Wrapper |
|---|---|---|---|
| `RT-IN-03` | GET `/inscripciones/{id}/pool` | `PoolPresenter` | `PoolOut` |
| `RT-IN-05` | POST `/inscripciones/{id}/participantes` | `ParticipanteAsignarPresenter` | `PoolOut` |
| `RT-IN-06` | DELETE `/inscripciones/{id}/participantes/{participacion_id}` | `ParticipanteRetirarPresenter` | `PoolOut` |
| `RT-CM-01` | POST `/inscripciones/{id}/compras/cupos` | `CompraCuposPresenter` | `CompraCreadaOut` |

Los nombres de presenter y wrapper de `RT-IN-03`, `RT-IN-05` y `RT-IN-06`
son los del registro congelado `SH-05`; este módulo los implementa con
`PoolPresenter` y publica el MISMO wrapper `PoolOut` en las tres rutas
(agregar y retirar devuelven el pool actualizado). La equivalencia de
nombres se pide su ratificación a A0.

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.
"""

from uuid import UUID

from injector import inject
from ninja_extra.permissions import IsAuthenticated
from ninja_jwt.authentication import JWTAuth
from ninja_extra import api_controller, route

from core.responses import ApiResponse, success_response
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    CompraCuposData,
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.services.orchestrators.compra_cupos_orchestrator import (
    CompraCuposOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.pool_orchestrator import (
    PoolOrchestrator,
)
from modules.salesianos_fest.presentation.presenters.compra_cupos_presenter import (
    CompraCuposPresenter,
)
from modules.salesianos_fest.presentation.presenters.inscripcion_presenter import (
    InscripcionPresenter,
)
from modules.salesianos_fest.presentation.presenters.pool_presenter import (
    PoolPresenter,
)
from modules.salesianos_fest.presentation.schemas.compra_cupos_schemas import (
    CompraCreadaOut,
    ComprarCuposIn,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    EquiposInscripcionOut,
    InscripcionDetalleOut,
    InscripcionInicialIn,
    InscripcionInicialOut,
)
from modules.salesianos_fest.presentation.schemas.pool_schemas import (
    ParticipanteAsignarIn,
    PoolOut,
)


@api_controller("/inscripciones", tags=["Inscripciones"])
class InscripcionController:
    """Inscripción deportiva del responsable."""

    @inject
    def __init__(
        self,
        orchestrator: InscripcionOrchestrator,
        pool_orchestrator: PoolOrchestrator,
        compra_cupos_orchestrator: CompraCuposOrchestrator,
    ):
        self.orchestrator = orchestrator
        self.pool_orchestrator = pool_orchestrator
        self.compra_cupos_orchestrator = compra_cupos_orchestrator

    @route.post(
        "",
        response={201: ApiResponse[InscripcionInicialOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Alta de la inscripción inicial y su compra pendiente.",
    )
    async def crear_inicial(self, request, payload: InscripcionInicialIn):
        """Route: POST /api/inscripciones

        Crea la inscripción del responsable autenticado, sus equipos y la
        COMPRA PENDIENTE de los cupos iniciales (`FL-03` paso 3).

        El precio es POR PERSONA (`D-CAT-01`): el cliente declara la
        cantidad de participantes, el servidor lo contrasta contra el mínimo
        comercial del paquete, resuelve el precio UNITARIO vigente y deriva
        el total como `cantidad × precio_unitario` (`RN-C02`).

        La categoría de los equipos la DERIVA el servidor desde la promoción
        (`D-CAT-05`): el cliente declara la promoción, nunca la categoría.

        La compra queda `PENDIENTE` y la inscripción nace con **cero cupos
        pagados**: una compra no pagada NO habilita cupos (`RN-I02`,
        `QA-I01`). El pago habilita EXACTAMENTE los cupos comprados en la
        ACTIVACIÓN de derechos, que es de `DOM-02`.

        Un reintento NO crea una segunda inscripción ni una segunda compra:
        devuelve la inscripción existente y su compra pendiente.
        """
        data = InscripcionInicialData(
            edicion_id=payload.edicion_id,
            paquete_id=payload.paquete_id,
            promocion_id=payload.promocion_id,
            fusion_promocion_id=payload.fusion_promocion_id,
            cantidad=payload.cantidad,
            cotizacion_version=payload.cotizacion_version,
            equipos=[
                EquipoCreateData(
                    disciplina_id=equipo.disciplina_id,
                    nombre=equipo.nombre,
                )
                for equipo in payload.equipos
            ],
        )
        result = await self.orchestrator.crear_inscripcion_inicial(
            request.auth,
            data,
        )
        return success_response(
            InscripcionPresenter.present_inicial(result),
            message="Inscripción registrada correctamente.",
        )

    @route.get(
        "/{inscripcion_id}",
        response={200: ApiResponse[InscripcionDetalleOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Detalle de una inscripción y su saldo de cupos.",
    )
    async def obtener(self, request, inscripcion_id: UUID):
        """Route: GET /api/inscripciones/{inscripcion_id}

        El saldo lo calcula el servidor (`RN-I03`): el cliente nunca resta.
        Sólo el responsable de la inscripción (o un administrador autorizado
        por el módulo) puede consultarla.
        """
        result = await self.orchestrator.obtener_inscripcion(
            request.auth,
            inscripcion_id,
        )
        return success_response(
            InscripcionPresenter.present_detalle(result),
            message="Inscripción consultada correctamente.",
        )

    @route.get(
        "/{inscripcion_id}/equipos",
        response={200: ApiResponse[EquiposInscripcionOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Equipos declarados en una inscripción.",
    )
    async def listar_equipos(self, request, inscripcion_id: UUID):
        """Route: GET /api/inscripciones/{inscripcion_id}/equipos"""
        equipos = await self.orchestrator.listar_equipos(
            request.auth,
            inscripcion_id,
        )
        return success_response(
            InscripcionPresenter.present_equipos(inscripcion_id, equipos),
            message="Equipos de la inscripción consultados correctamente.",
        )

    # ── DOM-02 · POOL, PARTICIPANTES Y AMPLIACIÓN ──────────────────────────

    @route.get(
        "/{inscripcion_id}/pool",
        response={200: ApiResponse[PoolOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Pool de cupos de una inscripción.",
    )
    async def obtener_pool(self, request, inscripcion_id: UUID):
        """Route: GET /api/inscripciones/{inscripcion_id}/pool

        `RT-IN-03`. La aritmética del pool la calcula el servidor: el
        wrapper lleva los TRES números (`pagados`, `asignados`,
        `disponibles`) y la lista de impedimentos. El cliente nunca resta
        (`SH-05` §1.3, `RN-I03`).
        """
        result = await self.pool_orchestrator.obtener_pool(
            request.auth,
            inscripcion_id,
        )
        return success_response(
            PoolPresenter.present_pool(result),
            message="Pool de la inscripción consultado correctamente.",
        )

    @route.post(
        "/{inscripcion_id}/participantes",
        response={200: ApiResponse[PoolOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Agrega un participante al pool de cupos.",
    )
    async def agregar_participante(
        self,
        request,
        inscripcion_id: UUID,
        payload: ParticipanteAsignarIn,
    ):
        """Route: POST /api/inscripciones/{inscripcion_id}/participantes

        `RT-IN-05`. Agrega una persona al pool y le asigna UN cupo pagado.

        Con `reemplaza_participacion_id` la operación es un MOVIMIENTO: la
        persona nueva toma el cupo de la retirada y ambas cosas ocurren en
        la misma transacción (`FL-05` paso 4, `RN-I04`).
        """
        data = ParticipanteAsignarData(
            persona_id=payload.persona_id,
            tipo_documento=payload.tipo_documento,
            numero_documento=payload.numero_documento,
            equipo_id=payload.equipo_id,
            rol=payload.rol,
            reemplaza_participacion_id=payload.reemplaza_participacion_id,
        )
        result = await self.pool_orchestrator.agregar_participante(
            request.auth,
            inscripcion_id,
            data,
        )
        return success_response(
            PoolPresenter.present_pool(result),
            message="Participante agregado al pool correctamente.",
        )

    @route.delete(
        "/{inscripcion_id}/participantes/{participacion_id}",
        response={200: ApiResponse[PoolOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Retira un participante y libera su cupo.",
    )
    async def retirar_participante(
        self,
        request,
        inscripcion_id: UUID,
        participacion_id: UUID,
    ):
        """Route: DELETE /api/inscripciones/{inscripcion_id}/participantes/{participacion_id}

        `RT-IN-06`. Retirar libera el cupo de ESA inscripción y NO anula la
        compra, NO devuelve dinero y NO altera el inventario (`RN-I04`,
        `DEC-06`).
        """
        result = await self.pool_orchestrator.retirar_participante(
            request.auth,
            inscripcion_id,
            participacion_id,
        )
        return success_response(
            PoolPresenter.present_pool(result),
            message="Participante retirado del pool correctamente.",
        )

    @route.post(
        "/{inscripcion_id}/compras/cupos",
        response={201: ApiResponse[CompraCreadaOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
        summary="Compra cupos extra para una inscripción.",
    )
    async def comprar_cupos(
        self,
        request,
        inscripcion_id: UUID,
        payload: ComprarCuposIn,
    ):
        """Route: POST /api/inscripciones/{inscripcion_id}/compras/cupos

        `RT-CM-01`. Crea una COMPRA SEPARADA de cupos extra vinculada a la
        MISMA inscripción (`FL-04` paso 2).

        El precio NO lo declara el cliente: lo resuelve el servidor contra
        el catálogo vigente (`RN-C02`). La compra queda `PENDIENTE` y los
        cupos se habilitan al confirmarse el pago (`RN-I02`).

        Un reintento con la misma cantidad devuelve la MISMA compra
        pendiente (`FR-04` I-4).
        """
        data = CompraCuposData(cantidad=payload.cantidad)
        result = await self.compra_cupos_orchestrator.comprar_cupos(
            request.auth,
            inscripcion_id,
            data,
        )
        return success_response(
            CompraCuposPresenter.present_compra(result),
            message="Compra de cupos registrada correctamente.",
        )


__all__ = ["InscripcionController"]
