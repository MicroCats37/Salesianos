"""
AsignacionCoreService — sync core operations for AsignacionCupo.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
from injector import inject

from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Inscripcion,
    InscripcionPersona,
)
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionPersonaChoices,
)


class AsignacionCoreService:
    """
    Core sync service for AsignacionCupo operations.

    Handles:
    - AsignacionCupo creation and state transitions
    - Saldo calculation for inscriptions
    """

    @inject
    def __init__(self):
        pass

    def crear_asignacion(
        self,
        inscripcion_id: str,
        inscripcion_persona_id: str,
        compra: Compra,
    ) -> AsignacionCupo:
        """
        Create a new AsignacionCupo for an active InscripcionPersona.

        Does NOT check saldo - caller (flujo) is responsible for that.
        """
        return AsignacionCupo.objects.create(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=inscripcion_persona_id,
            compra_id=compra.id,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        )

    def liberar_asignacion(
        self,
        asignacion: AsignacionCupo,
        motivo: str | None = None,
    ) -> AsignacionCupo:
        """
        Liberate an AsignacionCupo (retired player).
        """
        from django.utils import timezone

        asignacion.estado = EstadoAsignacionCupoChoices.LIBERADA
        asignacion.motivo = motivo
        asignacion.liberada_en = timezone.now()
        asignacion.save(update_fields=["estado", "motivo", "liberada_en", "updated_at"])
        return asignacion

    def revocar_asignacion(
        self,
        asignacion: AsignacionCupo,
        motivo: str | None = None,
    ) -> AsignacionCupo:
        """
        Revoke an AsignacionCupo (admin action).
        """
        asignacion.estado = EstadoAsignacionCupoChoices.REVOCADA
        asignacion.motivo = motivo
        asignacion.save(update_fields=["estado", "motivo", "updated_at"])
        return asignacion

    def obtener_asignacion_activa_por_inscripcion_persona(
        self,
        inscripcion_id: str,
        inscripcion_persona_id: str,
    ) -> AsignacionCupo | None:
        """Get the ACTIVA AsignacionCupo of an InscripcionPersona."""
        return (
            AsignacionCupo.objects
            .filter(
                inscripcion_id=inscripcion_id,
                inscripcion_persona_id=inscripcion_persona_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            .first()
        )

    def obtener_asignacion_activa_por_persona(
        self,
        inscripcion_id: str,
        persona_id: str,
    ) -> AsignacionCupo | None:
        """Get the ACTIVA AsignacionCupo of a person inside an inscripcion.

        The persona is resolved through its InscripcionPersona link, so the
        caller passes the *persona* id (not the InscripcionPersona id).
        """
        inscripcion_persona = (
            InscripcionPersona.objects
            .filter(
                inscripcion_id=inscripcion_id,
                persona_id=persona_id,
            )
            .first()
        )
        if inscripcion_persona is None:
            return None

        return self.obtener_asignacion_activa_por_inscripcion_persona(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=str(inscripcion_persona.id),
        )

    def obtener_asignacion_liberada(
        self,
        inscripcion_id: str,
        inscripcion_persona_id: str,
    ) -> AsignacionCupo | None:
        """Get the most recent LIBERADA AsignacionCupo of an InscripcionPersona."""
        return (
            AsignacionCupo.objects
            .filter(
                inscripcion_id=inscripcion_id,
                inscripcion_persona_id=inscripcion_persona_id,
                estado=EstadoAsignacionCupoChoices.LIBERADA,
            )
            .order_by("-created_at")
            .first()
        )

    def obtener_asignaciones_activas_por_compra(
        self,
        compra_id: str,
    ) -> list[AsignacionCupo]:
        """Get all active AsignacionCupo for a compra."""
        return list(
            AsignacionCupo.objects
            .filter(
                compra_id=compra_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            .select_related("inscripcion_persona", "inscripcion_persona__persona")
        )

    def contar_asignaciones_activas_compra(self, compra_id: str) -> int:
        """Count active AsignacionCupo for a compra."""
        return AsignacionCupo.objects.filter(
            compra_id=compra_id,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()

    def contar_pendientes_de_cupo(self, inscripcion_id: str) -> int:
        """Count the ACTIVO preregistrations of an inscripcion without a cup.

        These are the participants waiting in the pool: they hold no ACTIVA
        `AsignacionCupo`, so they cannot join a team yet.
        """
        con_derecho_ids = set(
            AsignacionCupo.objects.filter(
                inscripcion_id=inscripcion_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            ).values_list("inscripcion_persona_id", flat=True)
        )
        return InscripcionPersona.objects.filter(
            inscripcion_id=inscripcion_id,
            estado=EstadoInscripcionPersonaChoices.ACTIVO,
        ).exclude(id__in=con_derecho_ids).count()

    def listar_inscripciones_con_capacidad_pagada(self) -> list[str]:
        """Ids of the inscriptions that hold at least one PAGADA compra.

        Those are the only inscriptions that can have paid capacity to
        distribute — the entry point of the repair command.
        """
        return [
            str(inscripcion_id)
            for inscripcion_id in CompraInscripcion.objects.filter(
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .values_list("inscripcion_id", flat=True)
            .distinct()
        ]

    def calcular_saldo_inscripcion(self, inscripcion_id: str) -> dict:
        """
        Calculate saldo for an inscripcion.

        Returns dict with:
        - contratados: total cupos from PENDIENTE+PAGADA (not CANCELADA)
        - pagados: total cupos from PAGADA (not CANCELADA)
        - asignados_pagados: count of ACTIVA asignaciones from PAGADA compras
        - disponibles_pagados: pagados - asignados_pagados
        """
        compra_inscripciones = CompraInscripcion.objects.filter(
            inscripcion_id=inscripcion_id,
        ).exclude(compra__estado=EstadoCompraChoices.CANCELADA)

        contratados = sum(ci.cantidad for ci in compra_inscripciones)
        pagados = sum(
            ci.cantidad for ci in compra_inscripciones
            if ci.compra.estado == EstadoCompraChoices.PAGADA
        )

        # Asignaciones from PAGADA compras
        compras_pagadas_ids = [
            str(ci.compra_id) for ci in compra_inscripciones
            if ci.compra.estado == EstadoCompraChoices.PAGADA
        ]
        asignados_pagados = AsignacionCupo.objects.filter(
            compra_id__in=compras_pagadas_ids,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()

        disponibles_pagados = pagados - asignados_pagados

        return {
            "inscripcion_id": inscripcion_id,
            "contratados": contratados,
            "pagados": pagados,
            "asignados_pagados": asignados_pagados,
            "disponibles_pagados": max(0, disponibles_pagados),
        }

    def obtener_asignacion_por_id(self, asignacion_id: str) -> AsignacionCupo | None:
        """Get an AsignacionCupo by ID with select_related."""
        return (
            AsignacionCupo.objects
            .select_related("inscripcion", "compra", "inscripcion_persona", "inscripcion_persona__persona")
            .filter(id=asignacion_id)
            .first()
        )

    def listar_asignaciones_por_inscripcion(
        self,
        inscripcion_id: str,
    ) -> list[AsignacionCupo]:
        """List all AsignacionCupo for an inscripcion."""
        return list(
            AsignacionCupo.objects
            .select_related("compra", "inscripcion_persona", "inscripcion_persona__persona")
            .filter(inscripcion_id=inscripcion_id)
            .order_by("-created_at")
        )

    def obtener_compra_con_saldo_disponible(
        self,
        inscripcion_id: str,
    ) -> Compra | None:
        """
        Get a PAGADA commerce.Compra with available quota for assignment.

        Uses select_for_update to lock the row and prevent over-allocation.
        Returns None if no available quota.
        """
        # Get CompraInscripciones with PAGADA compra for this inscripcion
        compra_inscripciones = (
            CompraInscripcion.objects
            .filter(
                inscripcion_id=inscripcion_id,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .select_related("compra")
            .select_for_update()
            .order_by("created_at", "compra__referencia_externa", "compra_id")
        )

        for ci in compra_inscripciones:
            compra = ci.compra
            asignadas = self.contar_asignaciones_activas_compra(str(compra.id))
            if asignadas < ci.cantidad:
                return compra

        return None

    # ── Phase 4: derechos de cupo (asignacion determinista e idempotente) ──────

    @staticmethod
    def _elegir_compra_origen(
        orden_compra_ids: list[str],
        disponibles: dict[str, int],
        compra_preferida_id: str | None,
    ) -> str | None:
        """
        Pick the compra that funds the next assignment.

        The preferred compra (usually the one just confirmed) is consumed first
        so the buyer sees their payment used. The remaining sources are consumed
        in FIFO order (compra created_at) — the order is fixed, never random.
        """
        if compra_preferida_id and disponibles.get(compra_preferida_id, 0) > 0:
            return compra_preferida_id

        for compra_id in orden_compra_ids:
            if disponibles.get(compra_id, 0) > 0:
                return compra_id

        return None

    def asignar_cupos_a_preregistrados(
        self,
        inscripcion_id: str,
        compra_preferida_id: str | None = None,
    ) -> list[AsignacionCupo]:
        """
        Convert paid capacity into rights for the preregistered participants.

        Deterministic and idempotent:
        - Eligible: InscripcionPersona.estado=ACTIVO of this inscripcion without
          an ACTIVA AsignacionCupo. Participants over the paid capacity stay
          preregistered and blocked — no fictitious rights are created.
        - Order: (created_at, tipo_documento, numero_documento, id) — the
          earliest preregistration is served first and the document breaks the
          ties, so the allocation is reproducible for the same data.
        - Source of capacity: only PAGADA compras of this inscripcion. The
          per-compra limit (cantidad) is always respected.
        - Repeated calls create nothing new.

        Must be called inside a transaction (uses SELECT FOR UPDATE).

        Returns the list of created assignments (empty when there is nothing to do).
        """
        # Lock the paid compras of this inscripcion to prevent over-allocation.
        # The order is fixed (oldest compra first) so the allocation never
        # depends on the order in which the rows are returned by the database.
        compra_inscripciones = list(
            CompraInscripcion.objects
            .filter(
                inscripcion_id=inscripcion_id,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .select_related("compra")
            .select_for_update()
            .order_by(
                "compra__created_at",
                "compra__referencia_externa",
                "compra_id",
            )
        )
        if not compra_inscripciones:
            return []

        # Remaining capacity per compra.
        orden_compra_ids: list[str] = []
        disponibles: dict[str, int] = {}
        for ci in compra_inscripciones:
            compra_id = str(ci.compra_id)
            orden_compra_ids.append(compra_id)
            asignadas = self.contar_asignaciones_activas_compra(compra_id)
            disponibles[compra_id] = max(0, ci.cantidad - asignadas)

        total_disponible = sum(disponibles.values())
        if total_disponible <= 0:
            return []

        # Eligible participants (deterministic order).
        con_derecho_ids = {
            str(inscripcion_persona_id)
            for inscripcion_persona_id in AsignacionCupo.objects
            .filter(
                inscripcion_id=inscripcion_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            .values_list("inscripcion_persona_id", flat=True)
        }
        pendientes = [
            ip
            for ip in InscripcionPersona.objects
            .filter(
                inscripcion_id=inscripcion_id,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
            .select_related("persona")
            .order_by(
                "created_at",
                "persona__tipo_documento",
                "persona__numero_documento",
                "id",
            )
            if str(ip.id) not in con_derecho_ids
        ]

        creadas: list[AsignacionCupo] = []
        for ip in pendientes:
            if total_disponible <= 0:
                break

            origen = self._elegir_compra_origen(
                orden_compra_ids,
                disponibles,
                compra_preferida_id,
            )
            if origen is None:
                break

            asignacion = AsignacionCupo.objects.create(
                inscripcion_id=inscripcion_id,
                inscripcion_persona=ip,
                compra_id=origen,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )
            disponibles[origen] -= 1
            total_disponible -= 1
            creadas.append(asignacion)

        return creadas

    def reactivar_asignacion_liberada(
        self,
        asignacion: AsignacionCupo,
    ) -> AsignacionCupo | None:
        """
        Reactivate a LIBERADA assignment when the paid capacity still allows it.

        The original compra is preferred (same paid slot). When that compra has
        no free slot left, the assignment is moved to the oldest PAGADA compra
        with available capacity. When there is no capacity at all the
        assignment stays LIBERADA and None is returned — the participant keeps
        no right and stays blocked in the pool.
        """
        inscripcion_id = str(asignacion.inscripcion_id)
        origen = None

        # Prefer the original compra of the released right.
        compra_inscripcion = CompraInscripcion.objects.filter(
            compra_id=asignacion.compra_id,
        ).first()
        if compra_inscripcion is not None:
            compra_id = str(compra_inscripcion.compra_id)
            if compra_inscripcion.compra.estado == EstadoCompraChoices.PAGADA:
                asignadas = self.contar_asignaciones_activas_compra(compra_id)
                if asignadas < compra_inscripcion.cantidad:
                    origen = compra_inscripcion.compra

        # Fallback: any PAGADA compra of this inscripcion with free capacity.
        if origen is None:
            origen = self.obtener_compra_con_saldo_disponible(inscripcion_id)

        if origen is None:
            return None

        asignacion.estado = EstadoAsignacionCupoChoices.ACTIVA
        asignacion.compra = origen
        asignacion.motivo = None
        asignacion.liberada_en = None
        asignacion.save(
            update_fields=["estado", "compra", "motivo", "liberada_en", "updated_at"]
        )
        return asignacion
