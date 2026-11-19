"""`InscripcionCoreService` — escritura de la inscripción y sus equipos.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta el flujo).

La escritura de la inscripción NO habilita cupos: `cupos_pagados` nace en
cero y sólo la activación de derechos (DOM-02) lo incrementa (`RN-I02`).
"""

from modules.salesianos_fest.domain.models import Equipo, Inscripcion


class InscripcionCoreService:
    """Operaciones de persistencia de inscripciones y equipos."""

    def crear(
        self,
        *,
        edicion_id,
        responsable_id,
        paquete_id,
        referencia: str,
        cupos_solicitados: int,
    ) -> Inscripcion:
        """Crea la inscripción en estado `CREADA` y con cero cupos pagados.

        Args:
            edicion_id: UUID de la edición del alcance.
            responsable_id: UUID de la persona responsable.
            paquete_id: UUID del paquete contratado.
            referencia: referencia estable de la inscripción.
            cupos_solicitados: cupos que compra el alta.

        Returns:
            La inscripción creada.
        """
        return Inscripcion.objects.create(
            edicion_id=edicion_id,
            responsable_id=responsable_id,
            paquete_id=paquete_id,
            referencia=referencia,
            cupos_solicitados=cupos_solicitados,
            cupos_pagados=0,
            cupos_asignados=0,
        )

    def crear_equipos(self, inscripcion: Inscripcion, equipos: list) -> list[Equipo]:
        """Crea los equipos declarados en el alta.

        Args:
            inscripcion: la inscripción recién creada.
            equipos: lista de `EquipoCreateData`.

        Returns:
            Los equipos creados.
        """
        return [
            Equipo.objects.create(
                inscripcion=inscripcion,
                disciplina_id=equipo.disciplina_id,
                nombre=equipo.nombre,
            )
            for equipo in equipos
        ]


__all__ = ["InscripcionCoreService"]
