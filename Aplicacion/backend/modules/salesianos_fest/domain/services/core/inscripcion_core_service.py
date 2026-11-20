"""`InscripcionCoreService` — escritura de la inscripción y sus equipos.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta el flujo).

La escritura de la inscripción NO habilita cupos: `cupos_pagados` nace en
cero y sólo la activación de derechos (DOM-02) lo incrementa (`RN-I02`).

La CATEGORÍA de los equipos la recibe el servicio YA RESUELTA por el
flujo: el servicio no la decide y el cliente nunca la declara (`D-CAT-05`).
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
        promocion_id,
        referencia: str,
        cupos_solicitados: int,
        fusion_promocion_id=None,
    ) -> Inscripcion:
        """Crea la inscripción en estado `CREADA` y con cero cupos pagados.

        Args:
            edicion_id: UUID de la edición del alcance.
            responsable_id: UUID de la persona responsable.
            paquete_id: UUID del paquete contratado.
            promocion_id: UUID de la promoción (cohorte) que compra.
            referencia: referencia estable de la inscripción.
            cupos_solicitados: participantes que compra el alta.
            fusion_promocion_id: UUID de la promoción fusionada, o `None`.
                Es metadato DESCRIPTIVO (`D-CAT-02`).

        Returns:
            La inscripción creada.
        """
        return Inscripcion.objects.create(
            edicion_id=edicion_id,
            responsable_id=responsable_id,
            paquete_id=paquete_id,
            promocion_id=promocion_id,
            fusion_promocion_id=fusion_promocion_id,
            referencia=referencia,
            cupos_solicitados=cupos_solicitados,
            cupos_pagados=0,
            cupos_asignados=0,
        )

    def crear_equipos(
        self,
        inscripcion: Inscripcion,
        equipos: list,
        categoria,
    ) -> list[Equipo]:
        """Crea los equipos declarados en el alta.

        Args:
            inscripcion: la inscripción recién creada.
            equipos: lista de `EquipoCreateData`.
            categoria: la categoría YA DERIVADA por el servidor a partir de
                la promoción de la inscripción. El cliente no la declara.

        Returns:
            Los equipos creados.
        """
        return [
            Equipo.objects.create(
                inscripcion=inscripcion,
                disciplina_id=equipo.disciplina_id,
                categoria=categoria,
                nombre=equipo.nombre,
            )
            for equipo in equipos
        ]


__all__ = ["InscripcionCoreService"]
