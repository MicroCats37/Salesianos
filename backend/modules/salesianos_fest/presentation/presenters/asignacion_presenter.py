"""
AsignacionPresenter — transforms AsignacionCupo domain results to HTTP schemas.
"""
from modules.salesianos_fest.domain.models import AsignacionCupo
from modules.salesianos_fest.presentation.schemas.asignacion_schemas import (
    AsignarPersonaOut,
    LiberarCupoOut,
    SaldoOut,
    AsignacionDetailOut,
    AsignacionListOut,
)


class AsignacionPresenter:
    """Transform AsignacionCupo domain results to HTTP schemas."""

    @staticmethod
    def present_asignar_persona(result: dict) -> AsignarPersonaOut:
        """Transform asignar_persona result to schema."""
        return AsignarPersonaOut(
            asignacion_id=result["asignacion_id"],
            inscripcion_id=result["inscripcion_id"],
            persona_id=result["persona_id"],
            estado=result["estado"],
            compra_origen_id=result.get("compra_origen_id") or "",
        )

    @staticmethod
    def present_liberar_cupo(result: dict) -> LiberarCupoOut:
        """Transform liberar_cupo result to schema."""
        return LiberarCupoOut(
            inscripcion_id=result["inscripcion_id"],
            persona_id=result["persona_id"],
            asignacion_id=result.get("asignacion_id"),
            estado=result["estado"],
            cupo_liberado=bool(result.get("cupo_liberado", result["estado"] == "LIBERADA")),
        )

    @staticmethod
    def present_saldo(saldo: dict) -> SaldoOut:
        """Transform saldo result to schema."""
        return SaldoOut(
            inscripcion_id=saldo["inscripcion_id"],
            contratados=saldo["contratados"],
            pagados=saldo["pagados"],
            asignados_pagados=saldo["asignados_pagados"],
            disponibles_pagados=saldo["disponibles_pagados"],
        )

    @staticmethod
    def present_detail(asignacion: AsignacionCupo) -> AsignacionDetailOut:
        """Transform AsignacionCupo model to detail schema."""
        persona = asignacion.inscripcion_persona.persona
        return AsignacionDetailOut(
            id=str(asignacion.id),
            inscripcion_id=str(asignacion.inscripcion_id),
            compra_id=str(asignacion.compra_id),
            persona_id=str(persona.id),
            persona_nombre=f"{persona.nombres} {persona.apellidos}",
            estado=str(asignacion.estado),
            motivo=asignacion.motivo,
            liberada_en=asignacion.liberada_en.isoformat() if asignacion.liberada_en else None,
            created_at=asignacion.created_at.isoformat(),
        )

    @staticmethod
    def present_list(asignaciones: list[AsignacionCupo]) -> AsignacionListOut:
        """Transform list of AsignacionCupo to list schema."""
        return AsignacionListOut(
            asignaciones=[AsignacionPresenter.present_detail(a) for a in asignaciones]
        )
