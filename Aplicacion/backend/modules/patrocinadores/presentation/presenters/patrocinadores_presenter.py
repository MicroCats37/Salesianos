"""Presenters del módulo `patrocinadores` — result de dominio → schema HTTP.

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

Los presenters son TRANSFORMADORES PUROS: reciben un result object y
devuelven un schema HTTP. No consultan la base de datos, no llaman a
selectores y no construyen mensajes públicos de error.

El nombre del presenter es el que declara el ledger ruta → wrapper
(FR-07 §3.3): `PatrocinadorPresenter`, con el wrapper `PatrocinadorOut`.

SIN FINANZAS: el presenter NO expone aportaciones, comisiones, montos,
facturas ni datos de pago (ADM-21).
"""

from modules.patrocinadores.domain.results.patrocinadores_result import (
    PatrocinadorResult,
)
from modules.patrocinadores.presentation.schemas.patrocinadores_schemas import (
    PatrocinadorImagenOut,
    PatrocinadorLogoOut,
    PatrocinadorOut,
)


class PatrocinadorPresenter:
    """Presenter de `RT-MD-02` (alta de patrocinador)."""

    @staticmethod
    def present(result: PatrocinadorResult) -> PatrocinadorOut:
        """Proyecta el result de un patrocinador al wrapper HTTP."""
        return PatrocinadorOut(
            id=result.id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            nombre=result.nombre,
            slug=result.slug,
            descripcion=result.descripcion,
            sitio_web=result.sitio_web,
            visible=result.visible,
            logo=PatrocinadorPresenter.present_logo(result.logo),
            imagenes=[
                PatrocinadorPresenter.present_imagen(imagen) for imagen in result.imagenes
            ],
        )

    @staticmethod
    def present_logo(logo) -> PatrocinadorLogoOut | None:
        """Proyecta el logo de identidad al wrapper HTTP."""
        if logo is None:
            return None
        return PatrocinadorLogoOut(
            url=logo.url,
            disponible=logo.disponible,
        )

    @staticmethod
    def present_imagen(imagen) -> PatrocinadorImagenOut:
        """Proyecta una imagen de la galería al wrapper HTTP."""
        return PatrocinadorImagenOut(
            id=imagen.id,
            orden=imagen.orden,
            url=imagen.url,
            texto_alternativo=imagen.texto_alternativo,
            disponible=imagen.disponible,
            created_at=imagen.created_at,
        )


__all__ = [
    "PatrocinadorPresenter",
]
