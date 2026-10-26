"""Tests for InscripcionSelector with commerce composition.

Phase 1: Verifies the selector loads teams with discipline/minimum
and purchases with payment orders. NO derived state is calculated.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.models import OrdenPago
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    PaqueteBeneficio,
    Inscripcion,
    Equipo,
    InscripcionPersona,
    Participacion,
    CompraInscripcion,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
    EstadoInscripcionChoices,
    EstadoEquipoChoices,
    EstadoInscripcionPersonaChoices,
    TipoCompraChoices,
)
from modules.salesianos_fest.domain.selectors.inscripcion_selector import InscripcionSelector
from modules.salesianos_fest.domain.results.inscripcion_results import (
    EquipoResult,
    CompraResult,
    OrdenPagoResult,
)


# ─── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def evento_fixture(db):
    """Create a test evento."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def persona_fixture(db):
    """Create a test persona."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def disciplina_futbol_fixture(db):
    """Create a test disciplina: Fútbol 7 Masculino with min_jugadores=7."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_voley_fixture(db):
    """Create a test disciplina: Vóley Mixto with min_jugadores=6."""
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VOL",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=8,
        esta_activa=True,
    )


@pytest.fixture
def promocion_fixture(db):
    """Create a test promocion."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def categoria_fixture(db, evento_fixture, promocion_fixture):
    """Create a test categoria."""
    return Categoria.objects.create(
        evento=evento_fixture,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
    )


@pytest.fixture
def paquete_fixture(db, evento_fixture, disciplina_futbol_fixture, disciplina_voley_fixture):
    """Create a test paquete with two disciplinas."""
    paquete = Paquete.objects.create(
        evento=evento_fixture,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=2,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol_fixture)
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_voley_fixture)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    PaqueteBeneficio.objects.create(
        paquete=paquete,
        tipo=TipoBeneficioChoices.FIESTA,
        cantidad=1,
        alcance=AlcanceBeneficioChoices.INDIVIDUAL,
        modo_calculo=ModoCalculoBeneficioChoices.FIJO_INICIAL,
    )
    return paquete


@pytest.fixture
def inscripcion_fixture(
    db, evento_fixture, persona_fixture, paquete_fixture, promocion_fixture
):
    """Create a test inscripcion."""
    return Inscripcion.objects.create(
        evento=evento_fixture,
        responsable=persona_fixture,
        paquete=paquete_fixture,
        promocion=promocion_fixture,
        estado=EstadoInscripcionChoices.VALIDADA,
    )


@pytest.fixture
def equipo_fixture(
    db, inscripcion_fixture, disciplina_futbol_fixture, categoria_fixture, promocion_fixture
):
    """Create a test equipo with the futbol disciplina (min_jugadores=7)."""
    return Equipo.objects.create(
        inscripcion=inscripcion_fixture,
        disciplina=disciplina_futbol_fixture,
        categoria=categoria_fixture,
        promocion=promocion_fixture,
        nombre="Los Tigres FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def equipo_voley_fixture(
    db, inscripcion_fixture, disciplina_voley_fixture, categoria_fixture, promocion_fixture
):
    """Create a second equipo with the voley disciplina (min_jugadores=6)."""
    return Equipo.objects.create(
        inscripcion=inscripcion_fixture,
        disciplina=disciplina_voley_fixture,
        categoria=categoria_fixture,
        promocion=promocion_fixture,
        nombre="Los Halcones VC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def orden_pago_fixture(db):
    """Create a test orden de pago in PAGADA state."""
    return OrdenPago.objects.create(
        numero="OP-2026-001",
        monto_total=Decimal("400.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PAGADA,
        pagada_en=timezone.now(),
        descripcion="Pago inscripción FEST",
    )


@pytest.fixture
def compra_con_orden_fixture(db, persona_fixture, orden_pago_fixture):
    """Create a test Compra in PAGADA state with OrdenPago."""
    return Compra.objects.create(
        responsable=persona_fixture,
        descripcion="Compra inicial FEST",
        referencia_externa="FEST-INIT",
        total=Decimal("400.00"),
        estado=EstadoCompraChoices.PAGADA,
        orden_pago=orden_pago_fixture,
    )


@pytest.fixture
def compra_inscripcion_fixture(
    db, compra_con_orden_fixture, inscripcion_fixture
):
    """Link the Compra to the Inscripcion via CompraInscripcion."""
    return CompraInscripcion.objects.create(
        compra=compra_con_orden_fixture,
        inscripcion=inscripcion_fixture,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("40.00"),
        total=Decimal("400.00"),
    )


@pytest.fixture
def inscripcion_persona_fixture(db, inscripcion_fixture, persona_fixture):
    """Create an InscripcionPersona for participation."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_fixture,
        persona=persona_fixture,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def participacion_fixture(
    db, inscripcion_persona_fixture, equipo_fixture
):
    """Create a participation linking persona to equipo."""
    return Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_fixture,
        equipo=equipo_fixture,
        evento=equipo_fixture.inscripcion.evento,
        disciplina=equipo_fixture.disciplina,
        persona=inscripcion_persona_fixture.persona,
        rol="J",
        talla_camiseta="M",
        notas="",
        estado="A",
    )


# ─── Tests: Selector loads discipline minimum ───────────────────────────────────

@pytest.mark.django_db
def test_selector_carga_equipo_con_min_jugadores(
    inscripcion_fixture, equipo_fixture, disciplina_futbol_fixture
):
    """
    GIVEN: an inscripcion with an equipo linked to disciplina (min_jugadores=7)
    WHEN: get_by_id_with_details is called
    THEN: the returned EquipoResult includes disciplina.min_jugadores=7
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    assert len(result.equipos) == 1

    equipo_result = result.equipos[0]
    assert isinstance(equipo_result, EquipoResult)
    assert equipo_result.disciplina_nombre == "Fútbol 7 Masculino"
    assert equipo_result.min_jugadores == 7  # Disciplina.min_jugadores — NOT calculated


@pytest.mark.django_db
def test_selector_carga_multiple_equipos_con_sus_respectivos_minimos(
    inscripcion_fixture, equipo_fixture, equipo_voley_fixture,
    disciplina_futbol_fixture, disciplina_voley_fixture
):
    """
    GIVEN: an inscripcion with two equipos (futbol min=7, voley min=6)
    WHEN: get_by_id_with_details is called
    THEN: each equipo carries its own disciplina.min_jugadores
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    assert len(result.equipos) == 2

    equipos_dict = {e.nombre: e for e in result.equipos}

    assert equipos_dict["Los Tigres FC"].min_jugadores == 7
    assert equipos_dict["Los Halcones VC"].min_jugadores == 6


# ─── Tests: Selector loads commerce/payment data ───────────────────────────────

@pytest.mark.django_db
def test_selector_carga_compras_fest_con_orden_pago(
    inscripcion_fixture, compra_inscripcion_fixture, compra_con_orden_fixture,
    orden_pago_fixture
):
    """
    GIVEN: an inscripcion with a CompraInscripcion (Compra + OrdenPago in PAGADA)
    WHEN: get_by_id_with_details is called
    THEN: the result includes the CompraResult with its OrdenPagoResult
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    assert len(result.compras) == 1

    compra_result = result.compras[0]
    assert isinstance(compra_result, CompraResult)
    assert compra_result.tipo == "INICIAL"
    assert compra_result.cantidad == 10
    assert compra_result.precio_unitario == Decimal("40.00")
    assert compra_result.total == Decimal("400.00")
    assert compra_result.estado == "PAGADA"

    # OrdenPago is loaded
    assert compra_result.orden_pago is not None
    assert isinstance(compra_result.orden_pago, OrdenPagoResult)
    assert compra_result.orden_pago.numero == "OP-2026-001"
    assert compra_result.orden_pago.estado == "PAGADA"
    assert compra_result.orden_pago.pagada_en is not None


@pytest.mark.django_db
def test_selector_carga_compras_sin_orden_pago(
    db, inscripcion_fixture, persona_fixture
):
    """
    GIVEN: an inscripcion with a Compra without an OrdenPago (compra pendiente)
    WHEN: get_by_id_with_details is called
    THEN: the result includes CompraResult with orden_pago=None
    """
    # Create a pending Compra (no orden_pago)
    compra = Compra.objects.create(
        responsable=persona_fixture,
        descripcion="Compra pendiente",
        referencia_externa="FEST-PEND",
        total=Decimal("200.00"),
        estado=EstadoCompraChoices.PENDIENTE,
        orden_pago=None,  # No payment initiated yet
    )
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_fixture,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=5,
        precio_unitario=Decimal("40.00"),
        total=Decimal("200.00"),
    )

    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    assert len(result.compras) == 1

    compra_result = result.compras[0]
    assert compra_result.estado == "PENDIENTE"
    assert compra_result.orden_pago is None  # orden_pago may be null


# ─── Tests: Selector does NOT calculate derived state ───────────────────────────

@pytest.mark.django_db
def test_selector_no_calcula_estado_roster(
    inscripcion_fixture, equipo_fixture, inscripcion_persona_fixture,
    participacion_fixture, disciplina_futbol_fixture
):
    """
    GIVEN: an inscripcion with an equipo that has 1 active participacion (min=7)
    WHEN: get_by_id_with_details is called
    THEN: estado_roster is NOT present in the result
          (equipo_result only has min_jugadores; presenter calculates roster)
    """
    # 1 participacion, min_jugadores=7 → if presenter calculated, would be INCOMPLETO
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    equipo_result = result.equipos[0]

    # equipo_result has min_jugadores (data), but NOT estado_roster (derived)
    assert hasattr(equipo_result, "min_jugadores")
    assert hasattr(equipo_result, "disciplina_nombre")
    assert not hasattr(equipo_result, "estado_roster")  # NOT calculated by selector
    assert not hasattr(equipo_result, "faltantes")       # NOT calculated by selector
    assert not hasattr(equipo_result, "jugadores_registrados")  # NOT calculated


@pytest.mark.django_db
def test_selector_no_calcula_resumen_equipos(
    inscripcion_fixture, equipo_fixture
):
    """
    GIVEN: an inscripcion with equipos
    WHEN: get_by_id_with_details is called
    THEN: resumen_equipos is NOT present in the result
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    # InscripcionDetailResult does not have resumen_equipos attribute
    assert not hasattr(result, "resumen_equipos")


@pytest.mark.django_db
def test_selector_no_calcula_resumen_pago(
    inscripcion_fixture, compra_inscripcion_fixture
):
    """
    GIVEN: an inscripcion with a Compra in PAGADA state
    WHEN: get_by_id_with_details is called
    THEN: resumen_pago is NOT present in the result
          (presenter calculates estado_pago_global, message, etc.)
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    assert result is not None
    # inscripcion has compras loaded, but NO resumen_pago (derived)
    assert len(result.compras) == 1
    assert not hasattr(result, "resumen_pago")


# ─── Tests: Result objects have correct data types ─────────────────────────────

@pytest.mark.django_db
def test_compra_result_fields_are_typed_correctly(
    inscripcion_fixture, compra_inscripcion_fixture
):
    """
    GIVEN: a CompraResult is returned by the selector
    THEN: its fields have correct types (Decimal, not float)
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    compra_result = result.compras[0]
    assert isinstance(compra_result.precio_unitario, Decimal)
    assert isinstance(compra_result.total, Decimal)
    assert isinstance(compra_result.cantidad, int)


@pytest.mark.django_db
def test_equipo_result_min_jugadores_is_int(
    inscripcion_fixture, equipo_fixture, disciplina_futbol_fixture
):
    """
    GIVEN: an EquipoResult with disciplina.min_jugadores=7
    THEN: min_jugadores is an int (not a string or None)
    """
    result = InscripcionSelector.get_by_id_with_details(str(inscripcion_fixture.id))

    equipo_result = result.equipos[0]
    assert isinstance(equipo_result.min_jugadores, int)
    assert equipo_result.min_jugadores == 7
