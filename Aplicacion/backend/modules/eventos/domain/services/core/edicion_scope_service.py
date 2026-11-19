"""`EdicionScopeService` — la resolución de alcance de edición.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §8 (services)

Este archivo implementa el ORDEN ÚNICO de resolución congelado en FR-02 §2.2.
Es el reemplazo del supuesto global "evento activo por nombre".

    | # | Origen                              | Regla
    | 1 | `edicion_id` explícito             | Si no existe → 404 EDICION_NO_ENCONTRADA
    | 2 | Edición activa del actor            | Sólo si el actor tiene EXACTAMENTE una.
    |   |                                     | Varias → 409 EDICION_AMBIGUA
    | 3 | Edición PUBLICADA única            | Una → se usa. Cero → 404 EDICION_NO_PUBLICADA.
    |   |                                     | Varias → 409 EDICION_AMBIGUA
    | 4 | Sin resolución                      | 404 EDICION_NO_RESUELTA

REGLA DURA (FR-02 §2.2): en ningún nivel se resuelve la edición "la primera",
"la más reciente" o "la que coincida con un nombre por defecto". Ante
ambigüedad o ausencia se responde con error; nunca se opera sobre la edición
equivocada.

Niveles y responsabilidades:

- **Nivel 1** (`resolver_explicita`) NO hace fallback de ningún tipo: si el
  `edicion_id` no existe, la respuesta es 404. Es el nivel que usan las rutas
  con `edicion_id` en el path o en el query.
- **Nivel 2** (`resolver_actual`) recibe del llamador la lista de ediciones
  activas del actor. Ese origen NO se persiste en este módulo: FR-02 §3 no
  congela ninguna relación actor↔edición, de modo que el módulo aplica la
  REGLA ("exactamente una") sin inventar un modelo. El proveedor real lo
 conecta el módulo que posea esa relación (ver evidence FND-02 §"Decisiones
  abiertas").
- **Nivel 3** se aplica sólo cuando el llamador lo permite
  (`permitir_publicada_por_defecto=True`). Para una operación ADMINISTRATIVA
  el default es `False`: una escritura nunca debe caer por defecto sobre la
  edición publicada, porque eso mutaría la edición equivocada
  (`Aplicacion/plan/.../implementacion/01` §4, "Selección de edición — Nunca
  mutar inadvertidamente edición equivocada").
- **Nivel 4** es el cierre: no hay edición y no se puede elegir una.

Este módulo NO lee ninguna constante de settings.
"""

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.exceptions import (
    EdicionAmbiguaError,
    EdicionNoEncontradaError,
    EdicionNoPublicadaError,
    EdicionNoResueltaError,
)
from modules.eventos.domain.selectors.edicion_selector import EdicionSelector


class EdicionScopeService:
    """Resuelve la edición de alcance aplicando el orden congelado de FR-02 §2.2."""

    def __init__(self, selector: EdicionSelector = None):
        self.selector = selector or EdicionSelector()

    # ── Nivel 1 ─────────────────────────────────────────────────────────────

    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """Nivel 1: el `edicion_id` explícito. NUNCA hay fallback.

        `edicion_id` puede ser un `uuid.UUID` o su forma textual. Un valor
        mal formado NO es un error de servidor: es "no existe" (404).
        """
        edicion = self.selector.obtener_por_id(edicion_id)
        if edicion is None:
            raise EdicionNoEncontradaError()
        if exigir_publicada and edicion.estado != EstadoEdicion.PUBLICADA:
            raise EdicionNoPublicadaError()
        return edicion

    # ── Niveles 2 → 3 → 4 ───────────────────────────────────────────────────

    def resolver_actual(
        self,
        *,
        ediciones_activas_actor=None,
        exigir_publicada: bool = False,
        permitir_publicada_por_defecto: bool = True,
    ):
        """Niveles 2, 3 y 4 del orden congelado.

        Args:
            ediciones_activas_actor: iterable de ediciones que son las
                candidatas del actor (nivel 2). `None` significa "el actor no
                aporta candidatas" y el nivel 2 se omite.
            exigir_publicada: la edición devuelta debe estar `PUBLICADA`.
            permitir_publicada_por_defecto: si es `False`, el nivel 3 NO se
                aplica y la resolución termina en el nivel 4 cuando no hay
                candidatas del actor. Es el default seguro para operaciones
                administrativas.
        """
        candidatas = list(ediciones_activas_actor or [])

        # ── Nivel 2: edición activa del actor ──────────────────────────────
        if len(candidatas) > 1:
            raise EdicionAmbiguaError(candidatas=candidatas)
        if len(candidatas) == 1:
            return self._validar_publicada(candidatas[0], exigir_publicada)

        # ── Nivel 3: edición PUBLICADA única ───────────────────────────────
        if permitir_publicada_por_defecto:
            total = self.selector.contar_publicadas()
            if total > 1:
                raise EdicionAmbiguaError(
                    candidatas=list(self.selector.listar_publicadas())
                )
            if total == 1:
                publicada = self.selector.obtener_publicada()
                if publicada is not None:
                    return publicada
            else:
                # Cero publicadas: si además no existe ninguna edición, no
                # hay nada que resolver (nivel 4). Si existen ediciones pero
                # ninguna está publicada, la edición "no está publicada".
                if self.selector.contar() == 0:
                    raise EdicionNoResueltaError()
                raise EdicionNoPublicadaError()

        # ── Nivel 4: sin resolución ─────────────────────────────────────────
        raise EdicionNoResueltaError()

    # ── Utilidades ──────────────────────────────────────────────────────────

    @staticmethod
    def _validar_publicada(edicion, exigir_publicada: bool):
        if exigir_publicada and edicion.estado != EstadoEdicion.PUBLICADA:
            raise EdicionNoPublicadaError()
        return edicion


__all__ = ["EdicionScopeService"]
