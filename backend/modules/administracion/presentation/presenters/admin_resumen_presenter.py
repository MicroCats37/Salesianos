"""
AdminResumenPresenter — pure transformer of the operational overview.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps a result
object into the typed HTTP wrapper.
"""

from modules.administracion.domain.results.admin_resumen_results import (
    AdminResumenResult,
)
from modules.administracion.presentation.schemas.admin_resumen_schemas import (
    AdminAcreditacionesResumenOut,
    AdminAccesosResumenOut,
    AdminCuposResumenOut,
    AdminDisciplinaConteoOut,
    AdminEquiposResumenOut,
    AdminInscripcionesResumenOut,
    AdminPagosResumenOut,
    AdminParticipantesResumenOut,
    AdminResumenOut,
    EventoResumenOut,
)


class AdminResumenPresenter:
    """Transformers of the operational overview."""

    @staticmethod
    def present_resumen(result: AdminResumenResult) -> AdminResumenOut:
        """Map the overview result into its HTTP wrapper."""
        return AdminResumenOut(
            evento=EventoResumenOut(
                id=result.evento.id,
                nombre=result.evento.nombre,
                fecha_inicio=result.evento.fecha_inicio,
                fecha_fin=result.evento.fecha_fin,
                esta_activo=result.evento.esta_activo,
                fecha_limite_modificacion=result.evento.fecha_limite_modificacion,
                puede_modificar=result.evento.puede_modificar,
            ),
            inscripciones=AdminInscripcionesResumenOut(
                total=result.inscripciones.total,
                por_estado=result.inscripciones.por_estado,
                creadas_ultimos_7_dias=result.inscripciones.creadas_ultimos_7_dias,
            ),
            pagos=AdminPagosResumenOut(
                compras_total=result.pagos.compras_total,
                compras_pagadas=result.pagos.compras_pagadas,
                compras_pendientes=result.pagos.compras_pendientes,
                compras_canceladas=result.pagos.compras_canceladas,
                monto_pagado=result.pagos.monto_pagado,
                monto_pendiente=result.pagos.monto_pendiente,
                ordenes_vencidas=result.pagos.ordenes_vencidas,
                compras_pagadas_sin_liquidar=result.pagos.compras_pagadas_sin_liquidar,
            ),
            cupos=AdminCuposResumenOut(
                contratado=result.cupos.contratado,
                pagado=result.cupos.pagado,
                asignado_activo=result.cupos.asignado_activo,
                disponible_pagado=result.cupos.disponible_pagado,
                inscripciones_con_capacidad_exhaustada=(
                    result.cupos.inscripciones_con_capacidad_exhaustada
                ),
            ),
            equipos=AdminEquiposResumenOut(
                total=result.equipos.total,
                completos=result.equipos.completos,
                incompletos=result.equipos.incompletos,
                por_disciplina=[
                    AdminDisciplinaConteoOut(
                        disciplina_id=item.disciplina_id,
                        sigla=item.sigla,
                        nombre=item.nombre,
                        total=item.total,
                    )
                    for item in result.equipos.por_disciplina
                ],
            ),
            participantes=AdminParticipantesResumenOut(
                personas_distintas=result.participantes.personas_distintas,
                participaciones_activas=result.participantes.participaciones_activas,
                en_pool=result.participantes.en_pool,
                sin_cupo_activo=result.participantes.sin_cupo_activo,
            ),
            acreditaciones=AdminAcreditacionesResumenOut(
                total=result.acreditaciones.total,
                por_estado=result.acreditaciones.por_estado,
                con_acceso_fiesta=result.acreditaciones.con_acceso_fiesta,
                bloqueadas_por_admin=result.acreditaciones.bloqueadas_por_admin,
            ),
            accesos=AdminAccesosResumenOut(
                permitidos=result.accesos.permitidos,
                denegados=result.accesos.denegados,
                ultimo_acceso=result.accesos.ultimo_acceso,
            ),
        )


__all__ = ["AdminResumenPresenter"]
