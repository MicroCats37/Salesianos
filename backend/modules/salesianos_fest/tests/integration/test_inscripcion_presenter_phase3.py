"""Tests for InscripcionPresenter — Phase 3 (Lote 3).

Scope:
- Roster computation per team: estado_roster, jugadores_registrados,
  minimo_deportivo, faltantes (NO ORM access)
- Aggregate resumen_equipos: total, completos, incompletos
- Aggregate resumen_pago: counts, contracted/paid totals, disponible_pagado,
  estado_mensaje (NO ORM access)
- Payment state is orthogonal to Inscripcion.estado
- Metadata (OrdenPago.metadata, Compra.metadata) is never exposed
- GET /api/inscripciones/{id}/detalle returns 200 with Phase 2 schema fields

NO tests for: frontend, data migrations, unrelated state transitions.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

from modules.salesianos_fest.domain.results.inscripcion_results import (
    InscripcionDetailResult,
    EquipoResult,
    ParticipacionResult,
    CompraResult,
    OrdenPagoResult,
)
from modules.salesianos_fest.presentation.presenters.inscripcion_presenter import (
    InscripcionPresenter,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    EquipoDetailSchema,
    ResumenEquiposSchema,
    ResumenPagoSchema,
)


# ─── Helpers to build domain results ──────────────────────────────────────────

def make_participacion(
    pk: str,
    equipo_id: str,
    estado: str = "A",
    rol: str = "J",
) -> ParticipacionResult:
    """Build a ParticipacionResult with minimal data."""
    return ParticipacionResult(
        id=pk,
        inscripcion_persona_id=f"ip-{pk}",
        equipo_id=equipo_id,
        equipo_nombre="Equipo Test",
        evento_id="evt-1",
        disciplina_id="disc-1",
        disciplina_nombre="Fútbol 7",
        disciplina_sigla="F7",
        persona_id=f"per-{pk}",
        persona_nombre="Juan Pérez",
        persona_numero_documento="12345678",
        rol=rol,
        talla_camiseta="M",
        notas="",
        estado=estado,
        created_at=timezone.now(),
    )


def make_equipo(
    pk: str,
    inscripcion_id: str,
    min_jugadores: int,
    participaciones: list[ParticipacionResult],
) -> EquipoResult:
    """Build an EquipoResult."""
    return EquipoResult(
        id=pk,
        inscripcion_id=inscripcion_id,
        disciplina_id="disc-1",
        disciplina_nombre="Fútbol 7",
        disciplina_sigla="F7",
        min_jugadores=min_jugadores,
        categoria_id="cat-1",
        categoria_nombre="Juvenil",
        nombre=f"Equipo {pk}",
        estado="EQUIPO_ACTIVO",
        created_at=timezone.now(),
        participaciones=participaciones,
    )


def make_compra(
    pk: str,
    tipo: str,
    cantidad: int,
    precio_unitario: Decimal,
    estado: str,
    orden_estado: str = None,
    pagada_en: datetime = None,
) -> CompraResult:
    """Build a CompraResult with optional nested OrdenPago."""
    orden_pago = None
    if orden_estado is not None:
        orden_pago = OrdenPagoResult(
            id=f"op-{pk}",
            numero=f"OP-{pk}",
            estado=orden_estado,
            pagada_en=pagada_en,
        )
    return CompraResult(
        id=pk,
        tipo=tipo,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        total=precio_unitario * cantidad,
        estado=estado,
        orden_pago=orden_pago,
    )


def make_result(
    equipos: list[EquipoResult],
    compras: list[CompraResult],
    asignados_pagados: int = 0,
) -> InscripcionDetailResult:
    """Build a minimal InscripcionDetailResult."""
    return InscripcionDetailResult(
        id="insc-1",
        evento_id="evt-1",
        evento_nombre="Salesianos FEST 2026",
        responsable_id="per-1",
        responsable_nombre="Juan Pérez",
        paquete_id="pkg-1",
        paquete_nombre="Paquete Completo",
        promocion_id="promo-1",
        promocion_nombre="Juvenil",
        fusion_promocion_id=None,
        delegado_id=None,
        delegado_nombre=None,
        estado="RECIBIDA",
        observacion="",
        created_at=timezone.now(),
        equipos=equipos,
        personas=[],
        compras=compras,
        asignados_pagados=asignados_pagados,
    )


# ─── Roster computation (estado_roster, jugadores_registrados, faltantes) ─────

class TestRosterComputation:
    """Presenter computes roster state without ORM access."""

    def test_equipo_completo_when_jugadores_equal_minimo(self):
        """When activas == min_jugadores, estado_roster = COMPLETO."""
        p1 = make_participacion("p1", "eq-1")
        p2 = make_participacion("p2", "eq-1")
        p3 = make_participacion("p3", "eq-1")
        # min_jugadores=3, activas=3 → COMPLETO
        eq = make_equipo("eq-1", "insc-1", min_jugadores=3, participaciones=[p1, p2, p3])
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "COMPLETO"
        assert team.jugadores_registrados == 3
        assert team.faltantes == 0
        assert team.minimo_deportivo == 3

    def test_equipo_completo_when_jugadores_exceed_minimo(self):
        """When activas > min_jugadores, estado_roster = COMPLETO."""
        participaciones = [make_participacion(f"p{i}", "eq-1") for i in range(5)]
        # min_jugadores=3, activas=5 → COMPLETO
        eq = make_equipo("eq-1", "insc-1", min_jugadores=3, participaciones=participaciones)
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "COMPLETO"
        assert team.jugadores_registrados == 5
        assert team.faltantes == 0

    def test_equipo_incompleto_when_jugadores_below_minimo(self):
        """When activas < min_jugadores, estado_roster = INCOMPLETO."""
        p1 = make_participacion("p1", "eq-1")
        p2 = make_participacion("p2", "eq-1")
        # min_jugadores=7, activas=2 → INCOMPLETO
        eq = make_equipo("eq-1", "insc-1", min_jugadores=7, participaciones=[p1, p2])
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "INCOMPLETO"
        assert team.jugadores_registrados == 2
        assert team.faltantes == 5
        assert team.minimo_deportivo == 7

    def test_equipo_incompleto_when_no_activas(self):
        """When zero activas, estado_roster = INCOMPLETO."""
        eq = make_equipo("eq-1", "insc-1", min_jugadores=6, participaciones=[])
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "INCOMPLETO"
        assert team.jugadores_registrados == 0
        assert team.faltantes == 6

    def test_solo_cuenta_participaciones_activas(self):
        """Only ACTIVA participaciones are counted toward roster minimum."""
        # 1 ACTIVA + 1 RETIRADA + 1 CANCELADA → count=1
        p1 = make_participacion("p1", "eq-1", estado="A")
        p2 = make_participacion("p2", "eq-1", estado="RETIRADA")
        p3 = make_participacion("p3", "eq-1", estado="CANCELADA")
        # min_jugadores=3, activas=1 → INCOMPLETO
        eq = make_equipo("eq-1", "insc-1", min_jugadores=3, participaciones=[p1, p2, p3])
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "INCOMPLETO"
        assert team.jugadores_registrados == 1
        assert team.faltantes == 2

    def test_min_jugadores_default_zero_when_none(self):
        """When min_jugadores is None (not loaded), roster rules still work."""
        p1 = make_participacion("p1", "eq-1")
        eq = make_equipo("eq-1", "insc-1", min_jugadores=None, participaciones=[p1])
        # Patch to None after construction (simulating selector that didn't load it)
        eq.min_jugadores = None
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        assert team.estado_roster == "COMPLETO"  # 1 >= 0 (default)
        assert team.minimo_deportivo == 0
        assert team.faltantes == 0

    def test_estado_equipo_preserved_separate_from_estado_roster(self):
        """estado_equipo persists the raw equipo estado, distinct from estado_roster."""
        p1 = make_participacion("p1", "eq-1")
        eq = make_equipo("eq-1", "insc-1", min_jugadores=1, participaciones=[p1])
        eq.estado = "EQUIPO_CANCELADO"
        result = make_result(equipos=[eq], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        team = presented.equipos[0]

        # estado_equipo = persisted raw value
        assert team.estado_equipo == "EQUIPO_CANCELADO"
        # estado = backward-compat raw value (same as estado_equipo here)
        assert team.estado == "EQUIPO_CANCELADO"
        # estado_roster = derived
        assert team.estado_roster == "COMPLETO"


# ─── Aggregate resumen_equipos ───────────────────────────────────────────────

class TestResumenEquipos:
    """Presenter computes aggregate team roster summary."""

    def test_all_complete(self):
        """All teams COMPLETO → resumen_equipos reports all completos."""
        eq1 = make_equipo("eq-1", "insc-1", min_jugadores=3,
                           participaciones=[make_participacion(f"p{i}", "eq-1") for i in range(3)])
        eq2 = make_equipo("eq-2", "insc-1", min_jugadores=5,
                           participaciones=[make_participacion(f"p{i}", "eq-2") for i in range(5)])
        result = make_result(equipos=[eq1, eq2], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        summary = presented.resumen_equipos

        assert summary.total == 2
        assert summary.completos == 2
        assert summary.incompletos == 0

    def test_all_incomplete(self):
        """All teams INCOMPLETO → resumen_equipos reports all incompletos."""
        eq1 = make_equipo("eq-1", "insc-1", min_jugadores=5,
                           participaciones=[make_participacion("p1", "eq-1")])
        eq2 = make_equipo("eq-2", "insc-1", min_jugadores=7,
                           participaciones=[make_participacion("p2", "eq-2")])
        result = make_result(equipos=[eq1, eq2], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        summary = presented.resumen_equipos

        assert summary.total == 2
        assert summary.completos == 0
        assert summary.incompletos == 2

    def test_mixed(self):
        """Mixed complete/incomplete teams are counted correctly."""
        eq1 = make_equipo("eq-1", "insc-1", min_jugadores=3,
                           participaciones=[make_participacion(f"p{i}", "eq-1") for i in range(3)])  # COMPLETO
        eq2 = make_equipo("eq-2", "insc-1", min_jugadores=5,
                           participaciones=[make_participacion("pX", "eq-2")])  # INCOMPLETO
        result = make_result(equipos=[eq1, eq2], compras=[])

        presented = InscripcionPresenter.present_inscripcion_detail(result)
        summary = presented.resumen_equipos

        assert summary.total == 2
        assert summary.completos == 1
        assert summary.incompletos == 1


# ─── Aggregate resumen_pago ─────────────────────────────────────────────────

class TestResumenPago:
    """Presenter computes aggregate payment summary from compras/ordenes."""

    def _fmt_dt(self, dt: datetime) -> str:
        return dt.isoformat()

    def test_no_compras(self):
        """When inscripcion has no purchases, resumen_pago reflects empty state."""
        result = make_result(equipos=[], compras=[])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert pago.total_compras == 0
        assert pago.total_contratado == 0
        assert pago.total_pagado == 0.0
        assert pago.compras_pendientes == 0
        assert pago.compras_pagadas == 0
        assert pago.compras_canceladas == 0
        assert pago.disponible_pagado == 0
        assert pago.estado_mensaje == "Sin actividades de pago"
        assert pago.compras == []

    def test_all_cancelled(self):
        """All purchases CANCELADA → Sin actividades de pago."""
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="CANCELADA", orden_estado=None)
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert pago.total_compras == 1
        assert pago.compras_canceladas == 1
        assert pago.total_contratado == 0  # cancelled don't count
        assert pago.disponible_pagado == 0
        assert pago.estado_mensaje == "Sin actividades de pago"

    def test_pago_confirmado(self):
        """All active purchases PAGADA → Pago confirmado."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        c2 = make_compra("c2", tipo="AMPLIACION", cantidad=5,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        result = make_result(equipos=[], compras=[c1, c2])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert pago.total_compras == 2
        assert pago.compras_pagadas == 2
        assert pago.compras_pendientes == 0
        assert pago.compras_canceladas == 0
        assert pago.total_contratado == 15  # 10 + 5 (quantities)
        assert pago.total_pagado == 600.0  # (10*40) + (5*40) (monetary)
        assert pago.total_pagado_cantidad == 15  # paid quantities
        # disponible_pagado = free paid slots = paid_qty - active assignments
        #                      = 15 - 0 = 15
        assert pago.disponible_pagado == 15
        assert pago.estado_mensaje == "Pago confirmado"

    def test_pago_pendiente(self):
        """Active purchases all PENDIENTE → Pago pendiente."""
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PENDIENTE", orden_estado="PENDIENTE")
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert pago.total_compras == 1
        assert pago.compras_pendientes == 1
        assert pago.total_contratado == 10
        assert pago.total_pagado == 0.0
        assert pago.disponible_pagado == 0  # nothing paid yet
        assert pago.estado_mensaje == "Pago pendiente"

    def test_pago_parcial(self):
        """Mix of PAGADA and PENDIENTE → Pago parcial."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        c2 = make_compra("c2", tipo="AMPLIACION", cantidad=5,
                          precio_unitario=Decimal("40"), estado="PENDIENTE",
                          orden_estado="PENDIENTE")
        result = make_result(equipos=[], compras=[c1, c2])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert pago.total_compras == 2
        assert pago.compras_pagadas == 1
        assert pago.compras_pendientes == 1
        assert pago.total_contratado == 15  # 10 + 5 (quantities, non-cancelled)
        assert pago.total_pagado == 400.0  # 10*40 (monetary)
        assert pago.total_pagado_cantidad == 10  # paid quantity
        # disponible_pagado = free paid slots = paid_qty - active assignments
        #                      = 10 - 0 = 10
        # (the PENDIENTE amplification does NOT consume the paid slots)
        assert pago.disponible_pagado == 10
        assert pago.estado_mensaje == "Pago parcial"

    def test_disponible_pagado_computed_correctly(self):
        """disponible_pagado = paid_quantity - active assignments."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        # total_pagado (monetary) = 10 * 40 = 400
        # total_pagado_cantidad = 10
        # total_contratado = 10
        # disponible_pagado = max(0, 10 - 0) = 10
        assert pago.total_pagado == 400.0
        assert pago.total_pagado_cantidad == 10
        assert pago.total_contratado == 10
        assert pago.disponible_pagado == 10

    def test_pago_never_infers_inscripcion_estado(self):
        """Payment summary is computed independently of Inscripcion.estado."""
        # Create two results with different inscripcion estado values
        result1 = make_result(equipos=[], compras=[])
        result1.estado = "BORRADOR"

        result2 = make_result(equipos=[], compras=[])
        result2.estado = "CONFIRMADA"

        presented1 = InscripcionPresenter.present_inscripcion_detail(result1)
        presented2 = InscripcionPresenter.present_inscripcion_detail(result2)

        # resumen_pago must be identical regardless of inscripcion estado
        assert presented1.resumen_pago.estado_mensaje == presented2.resumen_pago.estado_mensaje
        assert presented1.resumen_pago.total_compras == presented2.resumen_pago.total_compras


# ─── Metadata exclusion ──────────────────────────────────────────────────────

class TestMetadataExclusion:
    """Presenter never exposes OrdenPago.metadata or Compra.metadata."""

    def test_orden_pago_metadata_not_exposed(self):
        """The orden_pago nested in compra resumen must not have a metadata field."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        orden = presented.resumen_pago.compras[0].orden_pago
        assert orden is not None
        assert not hasattr(orden, "metadata")

    def test_compra_metadata_not_exposed(self):
        """CompraResumenSchema must not have a metadata field."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        compra = presented.resumen_pago.compras[0]
        assert not hasattr(compra, "metadata")

    def test_resumen_pago_tree_has_no_metadata(self):
        """The entire resumen_pago tree must not expose metadata at any level."""
        now = timezone.now()
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA", pagada_en=now)
        result = make_result(equipos=[], compras=[c1])
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        pago = presented.resumen_pago
        assert not hasattr(pago, "metadata")
        if pago.compras:
            assert not hasattr(pago.compras[0], "metadata")
            if pago.compras[0].orden_pago:
                assert not hasattr(pago.compras[0].orden_pago, "metadata")


# ─── No ORM access ──────────────────────────────────────────────────────────

class TestPresenterNoORM:
    """InscripcionPresenter is a pure transformer — no ORM, no selectors."""

    def test_presenter_module_has_no_orm_objects_calls(self):
        """The presenter module source contains no .objects access or selector calls."""
        import inspect
        import modules.salesianos_fest.presentation.presenters.inscripcion_presenter as pm
        source = inspect.getsource(pm)

        # The presenter should NOT call any selector or ORM manager
        assert ".objects" not in source, "Presenter must not access .objects"
        assert "Selector" not in source, "Presenter must not call selectors"
        # The presenter should NOT access any ORM query methods
        forbidden = ["filter(", "get(", "create(", "update(", "delete("]
        for item in forbidden:
            assert item not in source, f"Presenter must not call ORM methods: {item}"

    def test_presenter_transforms_without_database_access(self):
        """present_inscripcion_detail produces correct output with no DB call."""
        # Uses only in-memory domain result objects
        eq = make_equipo("eq-1", "insc-1", min_jugadores=3,
                          participaciones=[make_participacion(f"p{i}", "eq-1") for i in range(3)])
        c1 = make_compra("c1", tipo="INICIAL", cantidad=10,
                          precio_unitario=Decimal("40"), estado="PAGADA",
                          orden_estado="PAGADA")
        result = make_result(equipos=[eq], compras=[c1])

        # This call must not touch the database
        presented = InscripcionPresenter.present_inscripcion_detail(result)

        assert presented.resumen_equipos.total == 1
        assert presented.resumen_pago.compras_pagadas == 1
        assert presented.equipos[0].estado_roster == "COMPLETO"
