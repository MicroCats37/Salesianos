"""Test configuration for salesianos_fest module."""
import pytest
from datetime import date
from decimal import Decimal

# Re-export of the centralized fixture library (TEST_ARCHITECTURE_CONTRACT §3.3).
from modules.salesianos_fest.tests.fixtures.genero_participacion_fixtures import (  # noqa: F401
    compra_pagada_genero,
    disciplina_modalidad_femenina,
    disciplina_modalidad_masculina,
    disciplina_modalidad_mixta,
    escenario_admin_genero_otra_edicion,
    escenario_admin_genero_sin_conflictos,
    escenario_auditoria_genero,
    escenario_auditoria_genero_limpio,
    escenario_auditoria_genero_otro_evento,
    escenario_genero_participacion,
    persona_genero_femenino,
    persona_genero_femenino_2,
    persona_genero_masculino,
    persona_genero_masculino_2,
    promocion_auditoria,
    usuario_responsable_genero,
)

# Catálogo independiente de pases de fiesta (Apply 1), su compra (Apply 2), su
# liquidación (Apply 3) y sus derechos nominativos (Apply 4).
from modules.salesianos_fest.tests.fixtures.pase_fixtures import (  # noqa: F401
    compra_pase_pagada,
    compra_pase_pagada_otro_lote,
    compra_pase_pendiente,
    evento_no_activo,
    pase_con_inventario_limitado,
    pase_de_edicion_inactiva,
    pase_fiesta,
    pase_inactivo,
    pase_precios_fuera_de_ventana,
    pase_sin_precio,
    persona_ajena,
    persona_beneficiaria_1,
    persona_beneficiaria_2,
    persona_beneficiaria_3,
    persona_beneficiaria_4,
    persona_beneficiaria_5,
    persona_comprador,
    persona_con_beneficio_deportivo,
    usuario_admin_pases,
    usuario_ajeno,
    usuario_comprador,
)

from django.test import Client

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    PaqueteBeneficio,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
)


@pytest.fixture
def api_client(db):
    """Django Client handles async controllers in the test transaction."""
    return Client()


@pytest.fixture
def evento(db):
    """Create a test evento."""
    return Evento.objects.create(
        nombre="Salesianos FEST Test 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol_m(db):
    """Create a test disciplina: Fútbol 7 Masculino."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_futbol_f(db):
    """Create a test disciplina: Fútbol 7 Femenino."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Femenino",
        sigla="F7F",
        modalidad=ModalidadChoices.FEMENINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_voley(db):
    """Create a test disciplina: Vóley Mixto."""
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VOL",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=8,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_basquet(db):
    """Create a test disciplina: Básquet Masculino."""
    return Disciplina.objects.create(
        nombre="Básquet Masculino",
        sigla="BAS",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=5,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def promocion_junior(db):
    """Create a test promocion: Junior."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def promocion_senior(db):
    """Create a test promocion: Senior."""
    return Promocion.objects.create(
        anio=1998,
        nombre="Senior",
        activa=True,
    )


@pytest.fixture
def categoria_senior(db, evento, promocion_senior):
    """Create a test categoria: Senior."""
    return Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
    )


@pytest.fixture
def paquete_reencuentro(db, evento):
    """Create a test paquete: Reencuentro + Fiesta."""
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
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date(2026, 11, 1),
        vigente_hasta=None,
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
def paquete_futbol(db, evento, disciplina_futbol_m):
    """Create a test paquete: Fútbol 7 masculino individual."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Fútbol 7 Masculino",
        descripcion="Torneo de fútbol 7",
        tipo=TipoPaqueteChoices.DISCIPLINA,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=7,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol_m)
    return paquete


@pytest.fixture
def paquete_duo(db, evento):
    """Create a test paquete: Dúo (sin disciplinas vinculadas)."""
    return Paquete.objects.create(
        evento=evento,
        nombre="Dúo + Fiesta Box",
        descripcion="Pack para dos personas",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=2,
        minimo_compra_inicial=15,
        activo=True,
    )
