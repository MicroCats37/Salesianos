"""`AdminAuditoriaPresenter` — la proyección HTTP del acta de auditoría.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El presenter publica el ACTA: quién, cuándo, qué y por qué. NO publica el
contexto crudo: el servicio ya lo saneó al escribir y la forma HTTP no tiene
ningún campo para el.

El `motivo` es la prosa del actor: se imprime VERBATIM, sin traducir.
"""

from modules.administracion.presentation.schemas.admin_auditoria_schemas import (
    AuditoriaItemOut,
    AuditoriaListadoOut,
)


class AdminAuditoriaPresenter:
    """Proyecta el acta del dominio a la forma HTTP."""

    @staticmethod
    def present_listado(resultado) -> AuditoriaListadoOut:
        """La forma HTTP de una página de actas."""
        return AuditoriaListadoOut(
            items=[
                AdminAuditoriaPresenter.present_item(item)
                for item in resultado.items
            ],
            total=resultado.total,
            page=resultado.page,
            page_size=resultado.page_size,
            total_pages=resultado.total_pages,
        )

    @staticmethod
    def present_item(item) -> AuditoriaItemOut:
        """La forma HTTP de un acta."""
        return AuditoriaItemOut(
            id=item.id,
            edicion_id=item.edicion_id,
            actor=item.actor,
            accion=item.accion,
            entidad=item.entidad,
            entidad_id=item.entidad_id,
            motivo=item.motivo,
            registrado_en=item.registrado_en,
        )


__all__ = ["AdminAuditoriaPresenter"]
