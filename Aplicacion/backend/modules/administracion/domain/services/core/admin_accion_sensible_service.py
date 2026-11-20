"""`AdminAccionSensibleService` — las REGLAS de una acción sensible del panel.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Un servicio core es sync y NO abre `transaction.atomic()`
(`contract/django-app-architecture-contract.md` §4.3): la transacción la abre
el flujo (`domain/services/flujos/admin_accion_sensible_flujo.py`).

## Las tres reglas de una acción sensible

1. **El MOTIVO es obligatorio.** Sin motivo la acción no se ejecuta: el
   422 `MOTIVO_REQUERIDO` se lanza ANTES de tocar nada.
2. **La VERSIÓN se comprueba cuando viaja.** El cliente puede enviar el
   token de versión del registro; si el registro cambió, el comando se
   rechaza con 409 `RESOURCE_CHANGED`. El backend NUNCA decide que un
   registro está fresco: el cliente tampoco.
3. **El ACTA se escribe.** La acción queda registrada con QUIÉN, CUÁNDO,
   QUÉ y POR QUÉ. El motivo viaja al acta y el acta es la prueba.

## Lo que este servicio NO hace

No ejecuta la acción: eso es del MÓDULO DUEÑO. Aquí sólo se valida y se
escribe el acta.
"""

from typing import Optional

from injector import inject

from core.exceptions import ConflictError, UnprocessableEntityError
from modules.administracion.domain.services.core.admin_auditoria_service import (
    AdminAuditoriaService,
)


class AdminAccionSensibleService:
    """Las reglas comunes de las acciones sensibles del panel."""

    @inject
    def __init__(self, auditoria_service: AdminAuditoriaService):
        self.auditoria_service = auditoria_service

    @staticmethod
    def validar_motivo(motivo: str) -> str:
        """El motivo limpio, o el 422 que lo impide.

        El motivo se exige ANTES de cualquier escritura: una acción sin
        motivo no se puede auditar y por tanto no se ejecuta.
        """
        texto = (motivo or "").strip()

        if not texto:
            raise UnprocessableEntityError(
                "La acción requiere un motivo.",
                code="MOTIVO_REQUERIDO",
            )

        return texto

    @staticmethod
    def version_de(registro) -> str:
        """El token de versión de un registro: su `updated_at`."""
        actualizado = getattr(registro, "updated_at", None)

        if actualizado is None:
            return ""

        return actualizado.isoformat()

    @classmethod
    def validar_version(cls, registro, version: Optional[str]) -> None:
        """La versión enviada, o el 409 que la invalida.

        Una versión VACÍA no se valida: el cliente no ha declarado ninguna
        expectativa de concurrencia y el backend no inventa una.
        """
        if not version:
            return

        if str(version) != cls.version_de(registro):
            raise ConflictError(
                "El registro cambió desde que se leyó. Vuelve a cargarlo e inténtalo de nuevo.",
                code="RESOURCE_CHANGED",
            )

    def registrar_acta(
        self,
        actor,
        accion: str,
        entidad: str,
        motivo: str,
        edicion_id=None,
        entidad_id: str = "",
        datos: Optional[dict] = None,
    ):
        """Escribe el ACTA de la acción sensible.

        El contexto auditable lo SANEA el servicio de auditoría: las claves
        prohibidas no se guardan nunca.
        """
        return self.auditoria_service.registrar(
            actor=actor,
            accion=accion,
            entidad=entidad,
            motivo=motivo,
            edicion_id=edicion_id,
            entidad_id=entidad_id,
            datos=datos,
        )


__all__ = ["AdminAccionSensibleService"]
