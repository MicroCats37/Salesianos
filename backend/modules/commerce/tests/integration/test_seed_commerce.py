"""
Integration tests for seed_commerce management command.

Batch 4 tests for commerce-refactor-clean-rebuild:
- Development guard: refuses non-DEBUG environments
- Idempotency: second run reuses existing records
- --clear: deletes commerce/FEST test data only, in dependency order
- Metadata: OrdenPago.metadata contains allowed keys only
- Scenarios: creates PENDIENTE initial, PAGADA expansion, CANCELADA expansion
"""
import pytest
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.conf import settings

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import OrdenPagoStatus, METADATA_ALLOWED_KEYS
from modules.salesianos_fest.domain.models import (
    Inscripcion,
    CompraInscripcion,
    AsignacionCupo,
)
from modules.salesianos_fest.domain.constants import TipoCompraChoices


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_debug_true(monkeypatch):
    """Temporarily set DEBUG=True."""
    monkeypatch.setattr(settings, "DEBUG", True)


@pytest.fixture
def mock_debug_false(monkeypatch):
    """Temporarily set DEBUG=False."""
    monkeypatch.setattr(settings, "DEBUG", False)


@pytest.fixture
def seed_catalog(db, mock_debug_true):
    """Seed catalog data (evento + paquetes) so seed_commerce can run.

    Does NOT call seed_commerce — callers must do so explicitly when needed.
    """
    from datetime import date
    from modules.eventos.domain.models import Evento
    from modules.salesianos_fest.domain.models import (
        Disciplina, Promocion, Paquete, PaqueteDisciplina, PaquetePrecio,
    )
    from modules.salesianos_fest.domain.constants import (
        ModalidadChoices, TipoPaqueteChoices, ModoDisciplinasChoices,
        EtapaChoices, TipoBeneficioChoices, AlcanceBeneficioChoices,
        ModoCalculoBeneficioChoices,
    )

    evento = Evento.objects.create(
        nombre="Salesianos FEST Test 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )
    promo = Promocion.objects.create(anio=2012, nombre="Junior", activa=True)
    disciplina = Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    return {"evento": evento, "promo": promo, "paquete": paquete, "disciplina": disciplina}


# ── Tests: Development Guard ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_seed_commerce_refuses_non_debug_environment(mock_debug_false):
    """
    GIVEN: DEBUG=False
    WHEN:  Running seed_commerce command
    THEN:  SystemExit is raised before any data is created.
    """
    with pytest.raises(SystemExit):
        call_command("seed_commerce")
    # Verify no data was created
    assert Compra.objects.count() == 0
    assert OrdenPago.objects.count() == 0


# ── Tests: Idempotency ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_seed_commerce_idempotent_second_run_creates_no_new_records(mock_debug_true, seed_catalog):
    """
    GIVEN: seed_catalog is set up
    WHEN:  Running seed_commerce once, then again (without --clear)
    THEN:  No new records are created; existing records are reused.
    """
    # First run
    call_command("seed_commerce")
    initial_compra_count = Compra.objects.count()
    initial_orden_pago_count = OrdenPago.objects.count()

    # Second run — should be idempotent
    call_command("seed_commerce")
    assert Compra.objects.count() == initial_compra_count
    assert OrdenPago.objects.count() == initial_orden_pago_count


@pytest.mark.django_db
def test_seed_commerce_idempotent_three_personas_each_with_three_compras(mock_debug_true, seed_catalog):
    """
    GIVEN: seed_catalog is set up
    WHEN:  Running seed_commerce once
    THEN:  Exactly 3 personas, 9 Compras (3 per persona: PENDIENTE, PAGADA, CANCELADA).
    """
    call_command("seed_commerce")

    # Should have exactly 3 test personas (DNI starts with 0000000)
    from modules.usuarios.domain.models.persona import Persona
    test_personas = Persona.objects.filter(numero_documento__startswith="0000000")
    assert test_personas.count() == 3

    # Should have exactly 9 Compras (3 per persona × 3 personas)
    assert Compra.objects.count() == 9

    # Verify the 3 scenario types
    pendientes = Compra.objects.filter(estado=EstadoCompraChoices.PENDIENTE)
    pagadas = Compra.objects.filter(estado=EstadoCompraChoices.PAGADA)
    canceladas = Compra.objects.filter(estado=EstadoCompraChoices.CANCELADA)
    assert pendientes.count() == 3
    assert pagadas.count() == 3
    assert canceladas.count() == 3


# ── Tests: --clear ──────────────────────────────────────────────────────────────

def _create_catalog_data():
    """Helper: create minimal catalog data (evento + paquete) for seed_commerce."""
    from datetime import date
    from decimal import Decimal
    from modules.eventos.domain.models import Evento
    from modules.salesianos_fest.domain.models import (
        Disciplina, Promocion, Paquete, PaqueteDisciplina, PaquetePrecio,
    )
    from modules.salesianos_fest.domain.constants import (
        ModalidadChoices, TipoPaqueteChoices, ModoDisciplinasChoices, EtapaChoices,
    )
    evento = Evento.objects.create(
        nombre="Salesianos FEST Test 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )
    promo = Promocion.objects.create(anio=2012, nombre="Junior", activa=True)
    disciplina = Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    return evento, paquete


@pytest.mark.django_db
def test_seed_commerce_clear_deletes_commerce_data_only(mock_debug_true):
    """
    GIVEN: Catalog data exists
    WHEN:  seed_commerce --clear is called (clear + reseed)
    THEN:  Old commerce data is replaced with fresh seed data.
    """
    _create_catalog_data()

    # First seed: create initial commerce data
    call_command("seed_commerce")
    initial_orden_nums = set(OrdenPago.objects.values_list("numero", flat=True))
    assert len(initial_orden_nums) == 9

    # --clear deletes old data AND reseeds (clear + seed = fresh data)
    call_command("seed_commerce", clear=True)

    # After --clear, new commerce data exists (different from initial)
    assert Compra.objects.count() == 9
    assert OrdenPago.objects.count() == 9
    assert Inscripcion.objects.count() == 3  # 1 per persona

    # Numeros should be different (fresh seed)
    new_orden_nums = set(OrdenPago.objects.values_list("numero", flat=True))
    assert new_orden_nums != initial_orden_nums


@pytest.mark.django_db
def test_seed_commerce_clear_resets_and_reseeds(mock_debug_true, seed_catalog):
    """
    GIVEN: seed_catalog is set up
    WHEN:  seed_commerce --clear then seed_commerce again
    THEN:  Data is recreated successfully.
    """
    call_command("seed_commerce")  # First seed
    initial_count = Compra.objects.count()
    assert initial_count > 0

    # --clear then seed again
    call_command("seed_commerce", clear=True)
    call_command("seed_commerce")
    assert Compra.objects.count() == initial_count


@pytest.mark.django_db
def test_seed_commerce_clear_idempotent(mock_debug_true):
    """
    GIVEN: Database is clean (no catalog data)
    WHEN:  Running seed_commerce --clear multiple times
    THEN:  No error; command succeeds (idempotent clear).
    """
    # --clear twice should be idempotent (no commerce data exists)
    call_command("seed_commerce", clear=True)  # First clear
    call_command("seed_commerce", clear=True)  # Second clear — should not error
    assert Compra.objects.count() == 0


# ── Tests: Scenarios ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_seed_commerce_creates_pending_initial_purchase(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  Creates PENDIENTE initial purchases with orden_pago assigned.
    """
    call_command("seed_commerce")

    pendientes = Compra.objects.filter(estado=EstadoCompraChoices.PENDIENTE)
    assert pendientes.count() == 3  # One per persona
    for compra in pendientes:
        assert compra.orden_pago is not None
        assert compra.orden_pago.estado == OrdenPagoStatus.PENDIENTE
        # Should have CompraInscripcion attached
        assert CompraInscripcion.objects.filter(compra=compra, tipo=TipoCompraChoices.INICIAL).exists()


@pytest.mark.django_db
def test_seed_commerce_creates_paid_expansion_with_transaction(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  Creates PAGADA expansion purchases with TransaccionPago.
    """
    call_command("seed_commerce")

    pagadas = Compra.objects.filter(estado=EstadoCompraChoices.PAGADA)
    assert pagadas.count() == 3  # One per persona
    for compra in pagadas:
        assert compra.orden_pago is not None
        assert compra.orden_pago.estado == OrdenPagoStatus.PAGADA
        # Should have TransaccionPago
        assert TransaccionPago.objects.filter(orden_pago=compra.orden_pago).exists()
        # Should have CompraInscripcion with AMPLIACION
        assert CompraInscripcion.objects.filter(
            compra=compra, tipo=TipoCompraChoices.AMPLIACION
        ).exists()


@pytest.mark.django_db
def test_seed_commerce_creates_cancelled_expansion(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  Creates CANCELADA expansion purchases.
    """
    call_command("seed_commerce")

    canceladas = Compra.objects.filter(estado=EstadoCompraChoices.CANCELADA)
    assert canceladas.count() == 3  # One per persona
    for compra in canceladas:
        assert compra.orden_pago is not None
        assert compra.orden_pago.estado == OrdenPagoStatus.CANCELADA
        # Should have CompraInscripcion with AMPLIACION
        assert CompraInscripcion.objects.filter(
            compra=compra, tipo=TipoCompraChoices.AMPLIACION
        ).exists()


# ── Tests: Metadata ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_seed_commerce_orden_pago_metadata_contains_allowed_keys(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  OrdenPago.metadata contains only keys from METADATA_ALLOWED_KEYS.
    """
    call_command("seed_commerce")

    for orden_pago in OrdenPago.objects.all():
        if orden_pago.metadata:
            for key in orden_pago.metadata.keys():
                assert key in METADATA_ALLOWED_KEYS, f"Key '{key}' not in METADATA_ALLOWED_KEYS"


@pytest.mark.django_db
def test_seed_commerce_orden_pago_metadata_has_required_fields(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  OrdenPago.metadata contains source, inscripcion_id, paquete_id, paquete_nombre, evento_id.
    """
    call_command("seed_commerce")

    for orden_pago in OrdenPago.objects.all():
        assert orden_pago.metadata is not None
        assert "source" in orden_pago.metadata
        assert orden_pago.metadata["source"] == "fest"
        assert "inscripcion_id" in orden_pago.metadata
        assert "paquete_id" in orden_pago.metadata
        assert "paquete_nombre" in orden_pago.metadata
        assert "evento_id" in orden_pago.metadata


@pytest.mark.django_db
def test_seed_commerce_orden_pago_metadata_has_buyer_snapshot(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  OrdenPago.metadata contains buyer_documento, buyer_nombres, buyer_apellidos.
    """
    call_command("seed_commerce")

    for orden_pago in OrdenPago.objects.all():
        assert orden_pago.metadata is not None
        assert "buyer_documento" in orden_pago.metadata
        assert "buyer_nombres" in orden_pago.metadata
        assert "buyer_apellidos" in orden_pago.metadata


# ── Tests: OrdenPago descripcion and referencia_externa ─────────────────────────

@pytest.mark.django_db
def test_seed_commerce_orden_pago_has_descripcion(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  Every OrdenPago has a non-empty descripcion.
    """
    call_command("seed_commerce")

    for orden_pago in OrdenPago.objects.all():
        assert orden_pago.descripcion is not None
        assert len(orden_pago.descripcion) > 0


@pytest.mark.django_db
def test_seed_commerce_orden_pago_has_referencia_externa(seed_catalog, mock_debug_true):
    """
    GIVEN: seed_catalog fixture
    WHEN:  Running seed_commerce
    THEN:  Every OrdenPago has a non-empty referencia_externa.
    """
    call_command("seed_commerce")

    for orden_pago in OrdenPago.objects.all():
        assert orden_pago.referencia_externa is not None
        assert len(orden_pago.referencia_externa) > 0


# ── Tests: Catalog Prerequisite ────────────────────────────────────────────────

@pytest.mark.django_db
def test_seed_commerce_requires_active_evento(mock_debug_true):
    """
    GIVEN: No active Evento exists
    WHEN:  Running seed_commerce
    THEN:  Command exits with error message; no data created.
    """
    # Ensure no active evento
    from modules.eventos.domain.models import Evento
    Evento.objects.all().update(esta_activo=False)

    # Capture output
    from io import StringIO
    out = StringIO()

    call_command("seed_commerce", stdout=out)
    output = out.getvalue()
    assert "No active Evento found" in output
    assert Compra.objects.count() == 0


@pytest.mark.django_db
def test_seed_commerce_requires_active_paquete(seed_catalog, mock_debug_true):
    """
    GIVEN: Active Evento but no active Paquete
    WHEN:  Running seed_commerce
    THEN:  Command exits with error message; no data created.
    """
    # Ensure no active paquete
    from modules.salesianos_fest.domain.models import Paquete
    Paquete.objects.all().update(activo=False)

    from io import StringIO
    out = StringIO()

    call_command("seed_commerce", stdout=out)
    output = out.getvalue()
    assert "No active Paquete found" in output
    assert Compra.objects.count() == 0
