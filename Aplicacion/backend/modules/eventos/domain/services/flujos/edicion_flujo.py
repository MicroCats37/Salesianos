"""`EdicionFlujo` — casos de uso completos de escritura sobre ediciones.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §4.4 (flujos)

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`
(`contract/django-app-architecture-contract.md` §4.4). El patrón es el
establecido en el proyecto: el método async envuelve la operación sync con
`sync_to_async` y la parte sync lleva el `@transaction.atomic()`.

Reglas que este flujo respeta:

- Toda escritura va contra una edición RESUELTA explícitamente
  (`resolver_explicita`, nivel 1 del orden congelado): una escritura nunca
  cae por defecto sobre "la edición publicada".
- La traducción de `IntegrityError` a excepción de dominio ocurre FUERA del
  bloque atómico, de modo que la transacción se revierte limpiamente y el
  error público es el del catálogo.
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.eventos.domain.exceptions import (
    EdicionPublicadaDuplicadaError,
    EdicionSlugDuplicadoError,
)
from modules.eventos.domain.schemas.edicion_schemas import EdicionCreateData
from modules.eventos.domain.services.core.edicion_core_service import EdicionCoreService
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService


class EdicionFlujo:
    """Casos de uso de escritura sobre ediciones."""

    @inject
    def __init__(
        self,
        core_service: EdicionCoreService,
        scope_service: EdicionScopeService,
    ):
        self.core_service = core_service
        self.scope_service = scope_service

    # ── Alta ────────────────────────────────────────────────────────────────

    async def crear_edicion(self, data: EdicionCreateData):
        """Crea una edición en estado `BORRADOR`."""
        try:
            return await sync_to_async(self._crear_edicion_sync)(data)
        except IntegrityError as exc:
            raise EdicionSlugDuplicadoError() from exc

    @transaction.atomic()
    def _crear_edicion_sync(self, data: EdicionCreateData):
        """Alta atómica de la edición."""
        return self.core_service.crear(data)

    # ── Publicación ─────────────────────────────────────────────────────────

    async def publicar_edicion(self, edicion_id):
        """Publica la edición indicada por `edicion_id`.

        El alcance es EXPLICITO (nivel 1): si la edición no existe, la
        respuesta es 404 y no se publica ninguna. La invariante de una única
        edición publicada por evento la impone la base de datos.
        """
        edicion = await sync_to_async(self.scope_service.resolver_explicita)(edicion_id)
        try:
            return await sync_to_async(self._publicar_edicion_sync)(edicion)
        except IntegrityError as exc:
            raise EdicionPublicadaDuplicadaError() from exc

    @transaction.atomic()
    def _publicar_edicion_sync(self, edicion):
        """Publicación atómica de la edición."""
        return self.core_service.publicar(edicion)

    # ── Cierre ──────────────────────────────────────────────────────────────

    async def cerrar_edicion(self, edicion_id):
        """Cierra la edición indicada por `edicion_id` (alcance explícito)."""
        edicion = await sync_to_async(self.scope_service.resolver_explicita)(edicion_id)
        return await sync_to_async(self.core_service.cerrar)(edicion)


__all__ = ["EdicionFlujo"]
