"""`EdicionPresenter` — result de dominio → schema HTTP.

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter) ·
          `contract/PLAN_REFACTORIZACION.md` §3.A

El presenter es un TRANSFORMADOR PURO: recibe un result object y devuelve un
schema HTTP. No consulta la base de datos, no llama a selectores y no
construye mensajes públicos de error.

Reglas:
- un método público por endpoint (`present`, `present_actual`);
- sólo `@staticmethod`;
- nada de `z.any()` ni campos genéricos: cada wrapper es tipado.
"""

from modules.eventos.domain.results.edicion_result import (
    EdicionActualResult,
    EdicionResult,
)
from modules.eventos.presentation.schemas.edicion_schemas import (
    EdicionActualOut,
    EdicionOut,
    ModuloHabilitadoOut,
)


class EdicionPresenter:
    """Transformador del módulo `eventos`."""

    @staticmethod
    def present(result: EdicionResult) -> EdicionOut:
        """Proyecta el result de una edición al wrapper HTTP."""
        return EdicionOut(
            id=result.id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            evento_id=result.evento_id,
            evento_nombre=result.evento_nombre,
            evento_slug=result.evento_slug,
            nombre=result.nombre,
            slug=result.slug,
            anio=result.anio,
            estado=result.estado,
            modulos_habilitados=list(result.modulos_habilitados or []),
            fecha_inicio=result.fecha_inicio,
            fecha_fin=result.fecha_fin,
        )

    @staticmethod
    def present_actual(result: EdicionActualResult) -> EdicionActualOut:
        """Proyecta el result de la edición vigente al wrapper HTTP.

        `FL-01` paso 1: el cliente recibe la edición resuelta y el estado de
        cada módulo lógico. Los módulos deshabilitados aparecen con
        `habilitado = False`: el apagado es información, no ausencia.
        """
        return EdicionActualOut(
            **EdicionPresenter.present(result.edicion).model_dump(),
            modulos=[
                ModuloHabilitadoOut(
                    clave=modulo.clave,
                    nombre=modulo.nombre,
                    habilitado=modulo.habilitado,
                )
                for modulo in result.modulos
            ],
        )


__all__ = ["EdicionPresenter"]
