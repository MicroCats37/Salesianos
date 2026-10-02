"""
AsignarDelegadoFlujo — async flow for assigning a delegate to an inscription.

Async flow — validates delegate eligibility before assignment.
"""

import asyncio

from django.db import transaction
from injector import inject

from modules.inscripciones.domain.models import Inscripcion
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
from modules.inscripciones.domain.services.core import validators


class AsignarDelegadoFlujo:
    """
    Async flow for assigning or replacing a delegate for an inscription.

    Validates that the delegate is either:
    - The inscription responsible, OR
    - A participant in any team of that inscription
    """

    @inject
    def __init__(self, inscripcion_svc: InscripcionService):
        self.inscripcion_svc = inscripcion_svc

    async def _asignar_delegado(
        self,
        inscripcion_id: str,
        persona_id: str,
    ):
        """
        Assign a delegate to an inscription.

        Args:
            inscripcion_id: UUID of the inscription.
            persona_id: UUID of the persona to assign as delegate.

        Returns:
            The created or updated InscripcionDelegado.

        Raises:
            InscripcionNotFoundError: If inscription not found.
            DelegadoInelegibleError: If persona is not eligible as delegate.
        """
        return await asyncio.to_thread(
            self._asignar_delegado_sync,
            inscripcion_id=inscripcion_id,
            persona_id=persona_id,
        )

    @transaction.atomic()
    def _asignar_delegado_sync(
        self,
        inscripcion_id: str,
        persona_id: str,
    ):
        """
        Sync version wrapped in transaction.atomic.
        """
        inscripcion = self.inscripcion_svc.obtener(inscripcion_id)
        if inscripcion is None:
            raise exc.InscripcionNotFoundError(f"Inscripcion {inscripcion_id} no encontrada.")

        # Validate eligibility
        is_eligible, reason = validators.validar_delegado_es_elegible(inscripcion, persona_id)
        if not is_eligible:
            raise exc.DelegadoInelegibleError(
                f"La persona no puede ser delegado: {reason}"
            )

        return self.inscripcion_svc.asignar_delegado(inscripcion_id, persona_id)

    async def _remover_delegado(self, inscripcion_id: str):
        """
        Remove the delegate from an inscription.

        Args:
            inscripcion_id: UUID of the inscription.
        """
        return await asyncio.to_thread(
            self._remover_delegado_sync,
            inscripcion_id,
        )

    @transaction.atomic()
    def _remover_delegado_sync(self, inscripcion_id: str):
        """Sync version."""
        deleted = self.inscripcion_svc.eliminar_delegado(inscripcion_id)
        if deleted == 0:
            raise exc.InscripcionNotFoundError(
                f"No se encontró delegado para la inscripción {inscripcion_id}."
            )
        return deleted
