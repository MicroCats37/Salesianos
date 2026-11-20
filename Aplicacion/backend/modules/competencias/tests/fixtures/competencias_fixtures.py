"""Fixtures del módulo `competencias`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures de ESTE módulo construyen su propia realidad: una edición, una
disciplina, inscripciones con sus equipos y su POOL (que es lo que decide la
elegibilidad, en `modules.salesianos_fest`).

**La elegibilidad NO se simula.** El adaptador real
(`EquipoElegibleAdapter`) consulta los modelos reales del dueño de la
inscripción: por eso las fixtures crean de verdad la inscripción, el equipo
y sus `Participacion` activas.

**No hay dobles.** Los tests ejercitan los servicios reales, resueltos por
el inyector real.

**Las inscripciones son DISTINTAS** porque `salesianos_fest` limita un
equipo por disciplina y POR INSCRIPCIÓN, y una inscripción viva por
(responsable, paquete) en la edición.
"""

from datetime import date, datetime

import pytest

from modules.competencias.domain.constants import EstadoEncuentro, EstadoRonda
from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)
from modules.eventos.domain.constants import EstadoEdicion, ModuloLogico
from modules.eventos.domain.models import Edicion, Evento
from modules.salesianos_fest.domain.constants import EstadoDisciplina
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    Participacion,
)
from modules.usuarios.domain.models import Persona, Usuario


# ── Edición ─────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    """Evento propietario de la edición del test."""
    return Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")


@pytest.fixture
def edicion_publicada(db, evento):
    """Edición `PUBLICADA` con el módulo `competencias` habilitado."""
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES, ModuloLogico.COMPETENCIAS],
    )


@pytest.fixture
def edicion_otra(db):
    """Una SEGUNDA edición publicada: permite comprobar el aislamiento."""
    otro_evento = Evento.objects.create(nombre="Otro FEST", slug="otro-fest")
    return Edicion.objects.create(
        evento=otro_evento,
        nombre="Otro FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES, ModuloLogico.COMPETENCIAS],
    )


# ── Catálogo e inscripción ──────────────────────────────────────────────────


@pytest.fixture
def disciplina(db, edicion_publicada):
    """Disciplina ACTIVA con un mínimo de UN participante por equipo."""
    return Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Vóley Mixto",
        slug="voley-mixto",
        minimo_por_equipo=1,
        maximo_por_equipo=12,
    )


@pytest.fixture
def disciplina_exigente(db, edicion_publicada):
    """Disciplina ACTIVA que exige TRES participantes por equipo."""
    return Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Fútbol 11",
        slug="futbol-11",
        minimo_por_equipo=3,
        maximo_por_equipo=11,
    )


@pytest.fixture
def disciplina_inactiva(db, edicion_publicada):
    """Disciplina `INACTIVA`: no puede frenar un torneo."""
    return Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Vóley Legacy",
        slug="voley-legacy",
        estado=EstadoDisciplina.INACTIVA,
    )


@pytest.fixture
def disciplina_otra_edicion(db, edicion_otra):
    """Disciplina de OTRA edición."""
    return Disciplina.objects.create(
        edicion=edicion_otra,
        nombre="Fútbol de Otro FEST",
        slug="futbol-otro",
        minimo_por_equipo=1,
    )


def _paquete(nombre, slug, edicion):
    """Paquete de inscripción de la edición."""
    return Paquete.objects.create(
        edicion=edicion,
        nombre=nombre,
        slug=slug,
        descripcion="Paquete de prueba.",
        cupos_incluidos=10,
    )


@pytest.fixture
def paquete(db, edicion_publicada):
    """Paquete de la edición publicada."""
    return _paquete("Paquete competitivo", "competitivo", edicion_publicada)


@pytest.fixture
def paquete_2(db, edicion_publicada):
    """SEGUNDO paquete: permite una segunda inscripción viva."""
    return _paquete("Paquete recycled", "recycled", edicion_publicada)


@pytest.fixture
def persona(db):
    """La persona responsable de la primera inscripción."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="11111111",
    )


@pytest.fixture
def persona_2(db):
    """La persona responsable de la segunda inscripción."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
    )


@pytest.fixture
def persona_3(db):
    """Una tercera persona, para el roster del segundo equipo."""
    return Persona.objects.create(
        nombres="María",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="33333333",
    )


@pytest.fixture
def persona_4(db):
    """Una cuarta persona, para el roster del equipo sin plantilla."""
    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="44444444",
    )


@pytest.fixture
def inscripcion(db, edicion_publicada, paquete, persona):
    """Inscripción viva con la capacidad pagada."""
    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete,
        referencia="INS-COMP-0001",
        cupos_solicitados=10,
        cupos_pagados=10,
        cupos_asignados=0,
    )


@pytest.fixture
def inscripcion_2(db, edicion_publicada, paquete_2, persona_2):
    """SEGUNDA inscripción viva: con otro responsable y otro paquete."""
    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona_2,
        paquete=paquete_2,
        referencia="INS-COMP-0002",
        cupos_solicitados=10,
        cupos_pagados=10,
        cupos_asignados=0,
    )


@pytest.fixture
def inscripcion_cancelada(db, edicion_publicada, paquete, persona_4):
    """Inscripción CANCELADA: su equipo no puede competir."""
    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona_4,
        paquete=paquete,
        referencia="INS-COMP-0003",
        estado="CANCELADA",
        cupos_solicitados=10,
        cupos_pagados=10,
        cupos_asignados=0,
    )


@pytest.fixture
def equipo(db, inscripcion, disciplina):
    """Equipo ACTIVO de la primera inscripción, con su disciplina."""
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        nombre="Equipo Vóley",
    )


@pytest.fixture
def equipo_2(db, inscripcion_2, disciplina):
    """SEGUNDO equipo, de otra inscripción y de la misma disciplina."""
    return Equipo.objects.create(
        inscripcion=inscripcion_2,
        disciplina=disciplina,
        nombre="Equipo Vóley B",
    )


@pytest.fixture
def equipo_cancelado(db, inscripcion_cancelada, disciplina):
    """Equipo de una inscripción CANCELADA."""
    return Equipo.objects.create(
        inscripcion=inscripcion_cancelada,
        disciplina=disciplina,
        nombre="Equipo Cancelado",
    )


@pytest.fixture
def equipo_otra_edicion(db, edicion_otra, disciplina_otra_edicion, persona):
    """Equipo de OTRA edición: no puede entrar en este torneo."""
    paquete_ajeno = _paquete("Paquete ajeno", "paquete-ajeno", edicion_otra)
    otra_inscripcion = Inscripcion.objects.create(
        edicion=edicion_otra,
        responsable=persona,
        paquete=paquete_ajeno,
        referencia="INS-AJENA-0001",
        cupos_solicitados=5,
        cupos_pagados=5,
        cupos_asignados=0,
    )
    return Equipo.objects.create(
        inscripcion=otra_inscripcion,
        disciplina=disciplina_otra_edicion,
        nombre="Equipo Ajeno",
    )


@pytest.fixture
def equipo_sin_plantilla(db, inscripcion, disciplina_exigente):
    """Equipo ACTIVO de OTRA disciplina y SIN roster: no puede competir."""
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_exigente,
        nombre="Equipo Sin Plantilla",
    )


@pytest.fixture
def equipo_plantilla_incompleta(db, inscripcion_2, disciplina_exigente):
    """Equipo de la disciplina exigente con sólo un participante activo."""
    return Equipo.objects.create(
        inscripcion=inscripcion_2,
        disciplina=disciplina_exigente,
        nombre="Equipo Plantilla Incompleta",
    )


@pytest.fixture
def participacion(db, equipo, persona):
    """Participación ACTIVA en el primer equipo: el equipo tiene plantilla."""
    return Participacion.objects.create(
        inscripcion=equipo.inscripcion,
        persona=persona,
        equipo=equipo,
        edicion=equipo.inscripcion.edicion,
        disciplina=equipo.disciplina,
        rol="JUGADOR",
        estado="ACTIVA",
    )


@pytest.fixture
def participacion_2(db, equipo_2, persona_3):
    """Participación ACTIVA en el segundo equipo."""
    return Participacion.objects.create(
        inscripcion=equipo_2.inscripcion,
        persona=persona_3,
        equipo=equipo_2,
        edicion=equipo_2.inscripcion.edicion,
        disciplina=equipo_2.disciplina,
        rol="JUGADOR",
        estado="ACTIVA",
    )


@pytest.fixture
def participacion_plantilla_incompleta(
    db,
    equipo_plantilla_incompleta,
    persona_3,
):
    """Único integrante de un equipo que requiere al menos tres personas."""
    return Participacion.objects.create(
        inscripcion=equipo_plantilla_incompleta.inscripcion,
        persona=persona_3,
        equipo=equipo_plantilla_incompleta,
        edicion=equipo_plantilla_incompleta.inscripcion.edicion,
        disciplina=equipo_plantilla_incompleta.disciplina,
        rol="JUGADOR",
        estado="ACTIVA",
    )


# ── Identidad ───────────────────────────────────────────────────────────────


@pytest.fixture
def usuario_admin(db, persona):
    """Cuenta con permisos de administración del área."""
    return Usuario.objects.create_user(
        username="admin",
        password="Prueba-12345",
        persona_fk=persona,
        is_staff=True,
    )


@pytest.fixture
def usuario_ajeno(db, persona_2):
    """Cuenta SIN permisos administrativos."""
    return Usuario.objects.create_user(
        username="ajeno",
        password="Prueba-12345",
        persona_fk=persona_2,
    )


# ── Cuadro ──────────────────────────────────────────────────────────────────


@pytest.fixture
def competencia(db, edicion_publicada, disciplina):
    """Competencia `PLANIFICADA` de la edición publicada."""
    return Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina,
        nombre="Vóley Mixto 2027",
        fecha=date(2027, 3, 14),
    )


@pytest.fixture
def ronda(db, competencia):
    """Ronda `ACTIVA` de la competencia."""
    return Ronda.objects.create(
        competencia=competencia,
        etiqueta="Cuartos de final",
        orden=1,
        estado=EstadoRonda.ACTIVA,
    )


@pytest.fixture
def ronda_final(db, competencia):
    """Segunda ronda: el destino del avance."""
    return Ronda.objects.create(
        competencia=competencia,
        etiqueta="Final",
        orden=2,
        estado=EstadoRonda.ACTIVA,
    )


@pytest.fixture
def encuentro(db, ronda):
    """Encuentro `BORRADOR`, vacío y sin horario: un borrador LEGÍTIMO."""
    return Encuentro.objects.create(
        ronda=ronda,
        orden=1,
        estado=EstadoEncuentro.BORRADOR,
    )


@pytest.fixture
def encuentro_final(db, ronda_final):
    """Encuentro `BORRADOR` de la ronda final: el destino del avance."""
    return Encuentro.objects.create(
        ronda=ronda_final,
        orden=1,
        estado=EstadoEncuentro.BORRADOR,
    )


@pytest.fixture
def equipo_en_cuadro(db, competencia, equipo, participacion):
    """La participación del primer equipo en el cuadro."""
    return CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo,
        orden=1,
        estado="ACTIVO",
    )


@pytest.fixture
def equipo_2_en_cuadro(db, competencia, equipo_2, participacion_2):
    """La participación del SEGUNDO equipo en el cuadro."""
    return CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_2,
        orden=2,
        estado="ACTIVO",
    )


# ── Utilidades ──────────────────────────────────────────────────────────────


@pytest.fixture
def jornada(db):
    """La franja horaria de la jornada, dentro del día de la competencia."""
    return {
        "inicio": datetime(2027, 3, 14, 10, 0),
        "fin": datetime(2027, 3, 14, 11, 0),
    }


@pytest.fixture
def jornada_posterior(db):
    """Una franja POSTERIOR, para el solapamiento."""
    return {
        "inicio": datetime(2027, 3, 14, 10, 30),
        "fin": datetime(2027, 3, 14, 11, 30),
    }


@pytest.fixture
def injector():
    """El inyector de dependencias del paquete DOM-07.

    Incluye los módulos de DI de los DUEÑOS que este módulo consume:
    `usuarios` (identidad y actor), `eventos` (alcance de edición),
    `pagos`, `commerce` (la interfaz comercial congelada) y
    `salesianos_fest` (la inscripción y el pool), MÁS el propio
    `CompetenciasModule`.
    """
    from injector import Injector

    from modules.commerce.di import CommerceModule
    from modules.competencias.di import CompetenciasModule
    from modules.eventos.di import EventosModule
    from modules.pagos.di import PagosModule
    from modules.salesianos_fest.di import SalesianosFestModule
    from modules.usuarios.di import UsuariosModule

    return Injector(
        [
            UsuariosModule,
            EventosModule,
            PagosModule,
            CommerceModule,
            SalesianosFestModule,
            CompetenciasModule,
        ]
    )


__all__ = [
    "competencia",
    "disciplina",
    "disciplina_exigente",
    "disciplina_inactiva",
    "disciplina_otra_edicion",
    "edicion_otra",
    "edicion_publicada",
    "encuentro",
    "encuentro_final",
    "equipo",
    "equipo_2",
    "equipo_2_en_cuadro",
    "equipo_cancelado",
    "equipo_en_cuadro",
    "equipo_otra_edicion",
    "equipo_sin_plantilla",
    "evento",
    "injector",
    "inscripcion",
    "inscripcion_2",
    "inscripcion_cancelada",
    "jornada",
    "jornada_posterior",
    "paquete",
    "paquete_2",
    "participacion",
    "participacion_2",
    "persona",
    "persona_2",
    "persona_3",
    "persona_4",
    "ronda",
    "ronda_final",
    "usuario_admin",
    "usuario_ajeno",
]
