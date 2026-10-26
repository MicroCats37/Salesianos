"""
AcreditacionPresenter — transforms AcreditacionEvento domain results to HTTP schemas.
"""
from modules.salesianos_fest.domain.models import AcreditacionEvento
from modules.salesianos_fest.domain.results.acreditacion_results import GenerarQRResult
from modules.salesianos_fest.presentation.schemas.acreditacion_schemas import (
    AcreditacionOut,
    OverrideFiestaOut,
    GenerarQROut,
    RegistrarAccesoOut,
)


class AcreditacionPresenter:
    """Transform AcreditacionEvento domain results to HTTP schemas."""

    @staticmethod
    def present_acreditacion(acreditacion: AcreditacionEvento) -> AcreditacionOut:
        """Transform AcreditacionEvento model to schema.

        The live QR credential is NOT mapped: `codigo_qr` is a bearer
        credential and only travels through the explicit, admin-only
        `present_generar_qr` action.
        """
        return AcreditacionOut(
            acreditacion_id=str(acreditacion.id),
            evento_id=str(acreditacion.evento_id),
            persona_id=str(acreditacion.persona_id),
            estado=str(acreditacion.estado),
            acceso_fiesta=acreditacion.acceso_fiesta,
            acceso_box=acreditacion.acceso_box,
            autorizacion_fiesta=str(acreditacion.autorizacion_fiesta),
            habilitado=acreditacion.habilitado,
            observacion=acreditacion.observacion or "",
        )

    @staticmethod
    def present_override(result: dict) -> OverrideFiestaOut:
        """Transform override result to schema."""
        return OverrideFiestaOut(
            persona_id=result["persona_id"],
            evento_id=result["evento_id"],
            autorizacion_fiesta=result["autorizacion_fiesta"],
            acceso_fiesta=result["acceso_fiesta"],
            observacion=result["observacion"],
        )

    @staticmethod
    def present_generar_qr(result: GenerarQRResult) -> GenerarQROut:
        """Transform the admin-only QR regeneration result to schema.

        This is the ONLY presenter that maps the live QR credential.
        """
        return GenerarQROut(
            acreditacion_id=result.acreditacion_id,
            codigo_qr=result.codigo_qr,
        )

    @staticmethod
    def present_registrar_acceso(result: dict) -> RegistrarAccesoOut:
        """Transform registrar_acceso result to schema."""
        return RegistrarAccesoOut(
            resultado=result["resultado"],
            persona=result.get("persona_nombre"),
            acceso_fiesta=result.get("acceso_fiesta", False),
            timestamp=result.get("timestamp") or "",
        )
