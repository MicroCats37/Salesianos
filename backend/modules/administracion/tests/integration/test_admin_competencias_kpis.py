"""
Integration tests — the KPI/alert aggregation of the bracket (Phase 3).

The administration area keeps ZERO tables: it only aggregates what
`modules.competencias` owns. These tests prove that the aggregation is
READ-ONLY, that it is scoped to ONE event and that the alerts point to the
real situations of the bracket.

The HTTP client is not involved: the aggregation is a READ aggregation of the
domain (`contract/api-wrapper-presenter-contract.md` §3).
"""
from datetime import date

import pytest

from modules.administracion.domain.selectors.admin_competencia_selector import (
    AdminCompetenciaSelector,
)
from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)
from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import (
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    ModalidadChoices,
    ModoDisciplinasChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    Promocion,
)
from modules.usuarios.domain.models.persona import Persona


@pytest.fixture
def selector_competencias():
    """The KPI/alert aggregation of the administration area."""
    return AdminCompetenciaSelector()


@pytest.fixture
def evento_kpi(db):
    """Event of the aggregation."""
    return Evento.objects.create(
        nombre="Salesianos FEST KPI 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def evento_kpi_ajeno(db):
    """Another event: its rows are NEVER counted."""
    return Evento.objects.create(
        nombre="Salesianos FEST KPI 2025",
        fecha_inicio=date(2025, 11, 15),
        fecha_fin=date(2025, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_kpi(db):
    """Discipline of the bracket of the aggregation."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 KPI",
        sigla="F7KPI",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def categoria_kpi(db, evento_kpi):
    """Category of the bracket of the aggregation."""
    return Categoria.objects.create(
        evento=evento_kpi,
        nombre="Sub-14 KPI",
        promocion_desde=2012,
        promocion_hasta=2013,
        esta_activa=True,
    )


@pytest.fixture
def competencia_kpi(db, evento_kpi, disciplina_kpi, categoria_kpi):
    """Competition of the aggregation."""
    return Competencia.objects.create(
        evento=evento_kpi,
        disciplina=disciplina_kpi,
        categoria=categoria_kpi,
        nombre="Eliminatoria KPI",
        fecha=date(2026, 11, 16),
        estado="PLANIFICADA",
    )


def _crear_equipo(evento, disciplina, nombre, documento) -> Equipo:
    """Create a team with its own enrollment (one team per enrollment)."""
    persona = Persona.objects.create(
        nombres="Responsable",
        apellidos="KPI",
        tipo_documento="DNI",
        numero_documento=documento,
        genero="M",
    )
    promocion = Promocion.objects.create(
        anio=int(documento[-2:]),
        nombre=f"KPI {documento}",
        activa=True,
    )
    paquete = Paquete.objects.create(
        evento=evento,
        nombre=f"Pack KPI {documento}",
        descripcion="Pack de las pruebas de los indicadores del cuadro",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    inscripcion = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        nombre=nombre,
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def equipo_kpi(db, evento_kpi, disciplina_kpi):
    """First team of the event of the aggregation."""
    return _crear_equipo(evento_kpi, disciplina_kpi, "Equipo KPI", "77889900")


@pytest.fixture
def equipo_kpi_2(db, evento_kpi, disciplina_kpi):
    """Second team of the event of the aggregation."""
    return _crear_equipo(evento_kpi, disciplina_kpi, "Equipo KPI II", "77889901")


# ── KPIs ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_kpi_de_competencias_cuenta_solo_el_evento(
    selector_competencias,
    evento_kpi,
    evento_kpi_ajeno,
    disciplina_kpi,
    categoria_kpi,
):
    """
    GIVEN: two events with one competition each
    WHEN: the aggregation runs for ONE event
    THEN: only the competitions of THAT event are counted
    """
    Competencia.objects.create(
        evento=evento_kpi,
        disciplina=disciplina_kpi,
        categoria=categoria_kpi,
        nombre="Eliminatoria KPI A",
        fecha=date(2026, 11, 16),
        estado="PLANIFICADA",
    )
    categoria_ajena = Categoria.objects.create(
        evento=evento_kpi_ajeno,
        nombre="Sub-14 KPI 2025",
        promocion_desde=2012,
        promocion_hasta=2013,
        esta_activa=True,
    )
    Competencia.objects.create(
        evento=evento_kpi_ajeno,
        disciplina=disciplina_kpi,
        categoria=categoria_ajena,
        nombre="Eliminatoria KPI B",
        fecha=date(2025, 11, 16),
        estado="PLANIFICADA",
    )

    conteo = selector_competencias.contar_competencias(str(evento_kpi.id))

    assert conteo["total"] == 1
    assert conteo["por_estado"] == {"PLANIFICADA": 1}
    assert conteo["con_rondas"] == 0
    assert conteo["con_equipos"] == 0


@pytest.mark.django_db
def test_kpi_de_encuentros_cuenta_los_estados(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
):
    """
    GIVEN: a bracket with one scheduled encounter and one without a schedule
    WHEN: the aggregation runs
    THEN: the counters of the states and of the unscheduled ones are right
    """
    ronda = Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )
    Encuentro.objects.create(ronda=ronda, orden=1, estado="BORRADOR")
    Encuentro.objects.create(ronda=ronda, orden=2, estado="FINALIZADO")

    conteo = selector_competencias.contar_encuentros(str(evento_kpi.id))

    assert conteo["total"] == 2
    assert conteo["por_estado"] == {"BORRADOR": 1, "FINALIZADO": 1}
    assert conteo["sin_horario"] == 2
    assert conteo["finalizados"] == 1
    assert conteo["byes"] == 0
    assert conteo["rondas"] == 1


@pytest.mark.django_db
def test_kpi_de_equipos_solo_cuenta_los_activos(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
    equipo_kpi,
    equipo_kpi_2,
):
    """
    GIVEN: an active team and a withdrawn one in the bracket
    WHEN: the aggregation runs
    THEN: the withdrawn team is not part of the operation
    """
    CompetenciaEquipo.objects.create(
        competencia=competencia_kpi,
        equipo=equipo_kpi,
        orden=1,
        estado="ACTIVO",
    )
    CompetenciaEquipo.objects.create(
        competencia=competencia_kpi,
        equipo=equipo_kpi_2,
        orden=2,
        estado="RETIRADO",
    )

    conteo = selector_competencias.contar_equipos(str(evento_kpi.id))

    assert conteo["total"] == 2
    assert conteo["activos"] == 1
    assert conteo["retirados"] == 1


# ── Alertas ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_alerta_de_un_cuadro_sin_equipos(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
):
    """
    GIVEN: a competition with rounds but without teams
    WHEN: the aggregation runs
    THEN: the alert `CUADRO_SIN_EQUIPOS` is reported
    """
    Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )

    alertas = selector_competencias.listar_alertas(str(evento_kpi.id))

    alerta = next(
        (a for a in alertas if a["codigo"] == "CUADRO_SIN_EQUIPOS"), None
    )
    assert alerta is not None
    assert alerta["cantidad"] == 1
    assert alerta["mensaje"]


@pytest.mark.django_db
def test_alerta_de_un_encuentro_sin_participante(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
):
    """
    GIVEN: a scheduled encounter with an empty slot
    WHEN: the aggregation runs
    THEN: the alert `ENCUENTRO_SIN_PARTICIPANTE` is reported
    """
    ronda = Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )
    Encuentro.objects.create(ronda=ronda, orden=1, estado="PROGRAMADO")

    alertas = selector_competencias.listar_alertas(str(evento_kpi.id))

    alerta = next(
        (a for a in alertas if a["codigo"] == "ENCUENTRO_SIN_PARTICIPANTE"), None
    )
    assert alerta is not None
    assert alerta["cantidad"] == 1


@pytest.mark.django_db
def test_alerta_de_un_ganador_no_propagado(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
    equipo_kpi,
):
    """
    GIVEN: a finished encounter whose winner never reached the linked slot
    WHEN: the aggregation runs
    THEN: the alert `GANADOR_NO_PROPAGADO` is reported
    """
    ronda = Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )
    ronda_siguiente = Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Semifinal",
        orden=2,
        estado="ACTIVA",
    )
    entrada = CompetenciaEquipo.objects.create(
        competencia=competencia_kpi,
        equipo=equipo_kpi,
        orden=1,
        estado="ACTIVO",
    )
    origen = Encuentro.objects.create(
        ronda=ronda,
        orden=1,
        participante_1=entrada,
        estado="FINALIZADO",
        ganador=entrada,
    )
    destino = Encuentro.objects.create(
        ronda=ronda_siguiente,
        orden=1,
        estado="BORRADOR",
    )
    origen.siguiente_encuentro = destino
    origen.slot_destino = "PARTICIPANTE_1"
    origen.save()

    alertas = selector_competencias.listar_alertas(str(evento_kpi.id))

    alerta = next(
        (a for a in alertas if a["codigo"] == "GANADOR_NO_PROPAGADO"), None
    )
    assert alerta is not None
    assert alerta["cantidad"] == 1


@pytest.mark.django_db
def test_la_agregacion_no_escribe_nada(
    selector_competencias,
    evento_kpi,
    competencia_kpi,
):
    """
    GIVEN: a competition with a round of the event
    WHEN: the aggregation runs
    THEN: NOTHING is written (it is a READ aggregation)
    """
    Ronda.objects.create(
        competencia=competencia_kpi,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )

    antes = (
        Competencia.objects.count(),
        Ronda.objects.count(),
        Encuentro.objects.count(),
        CompetenciaEquipo.objects.count(),
    )

    selector_competencias.contar_competencias(str(evento_kpi.id))
    selector_competencias.contar_equipos(str(evento_kpi.id))
    selector_competencias.contar_encuentros(str(evento_kpi.id))
    selector_competencias.listar_alertas(str(evento_kpi.id))

    despues = (
        Competencia.objects.count(),
        Ronda.objects.count(),
        Encuentro.objects.count(),
        CompetenciaEquipo.objects.count(),
    )
    assert antes == despues
