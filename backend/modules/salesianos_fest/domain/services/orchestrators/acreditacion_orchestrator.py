"""
AcreditacionOrchestrator — async thin facade for AcreditacionEvento operations.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.
"""
from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.services.flujos.override_fiesta_flujo import OverrideFiestaFlujo
from modules.salesianos_fest.domain.services.flujos.registrar_acceso_flujo import RegistrarAccesoFlujo
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.results.acreditacion_results import (
    OverrideFiestaResult,
    AccesoRegistradoResult,
    AcreditacionResult,
    GenerarQRResult,
)


class AcreditacionOrchestrator:
    """
    Thin async facade for AcreditacionEvento operations.
    """

    @inject
    def __init__(
        self,
        override_fiesta_flujo: OverrideFiestaFlujo,
        registrar_acceso_flujo: RegistrarAccesoFlujo,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.override_fiesta_flujo = override_fiesta_flujo
        self.registrar_acceso_flujo = registrar_acceso_flujo
        self.acreditacion_core = acreditacion_core

    async def aplicar_override_fiesta(
        self,
        evento_id: str,
        persona_id: str,
        autorizacion: str,
        motivo: str,
    ) -> OverrideFiestaResult:
        """
        Apply admin override for fiesta access.

        See OverrideFiestaFlujo._aplicar_override for full docs.
        """
        result = await self.override_fiesta_flujo._aplicar_override(
            evento_id, persona_id, autorizacion, motivo
        )
        return OverrideFiestaResult(
            persona_id=result["persona_id"],
            evento_id=result["evento_id"],
            autorizacion_fiesta=result["autorizacion_fiesta"],
            acceso_fiesta=result["acceso_fiesta"],
            observacion=result["observacion"],
        )

    async def registrar_acceso(
        self,
        qr_token: str,
        punto_acceso: str | None = None,
        operador_id: int | None = None,
    ) -> AccesoRegistradoResult:
        """
        Register an access attempt via QR scan.

        See RegistrarAccesoFlujo._registrar_acceso for full docs.
        """
        result = await self.registrar_acceso_flujo._registrar_acceso(
            qr_token, punto_acceso, operador_id
        )
        return AccesoRegistradoResult(
            resultado=result["resultado"],
            persona_nombre=result.get("persona_nombre"),
            acceso_fiesta=result.get("acceso_fiesta", False),
            timestamp=result.get("timestamp"),
        )

    async def obtener_acreditacion(
        self,
        evento_id: str,
        persona_id: str,
    ) -> AcreditacionResult | None:
        """
        Get acreditacion for an evento/persona.
        """
        obtener = sync_to_async(
            self.acreditacion_core.obtener_acreditacion_por_evento_persona,
            thread_sensitive=True,
        )
        acreditacion = await obtener(evento_id, persona_id)
        if acreditacion is None:
            return None
        return AcreditacionResult(
            acreditacion_id=str(acreditacion.id),
            evento_id=str(acreditacion.evento_id),
            persona_id=str(acreditacion.persona_id),
            estado=str(acreditacion.estado),
            acceso_fiesta=acreditacion.acceso_fiesta,
            autorizacion_fiesta=str(acreditacion.autorizacion_fiesta),
            habilitado=acreditacion.habilitado,
        )

    async def regenerar_qr(
        self,
        evento_id: str,
        persona_id: str,
    ) -> GenerarQRResult | None:
        """
        Regenerate the live QR credential of an acreditacion.

        Admin-only delivery action: the credential is returned here and NOWHERE
        else. The general read never exposes it. Returns None when the
        acreditacion does not exist — the controller owns the 404 answer.
        """
        obtener = sync_to_async(
            self.acreditacion_core.obtener_acreditacion_por_evento_persona,
            thread_sensitive=True,
        )
        acreditacion = await obtener(evento_id, persona_id)
        if acreditacion is None:
            return None

        regenerar = sync_to_async(
            self.acreditacion_core.regenarar_qr,
            thread_sensitive=True,
        )
        acreditacion = await regenerar(acreditacion)
        return GenerarQRResult(
            acreditacion_id=str(acreditacion.id),
            codigo_qr=str(acreditacion.codigo_qr),
        )
