"""
Fixtures for the discipline/gender participation compatibility audit.

The audit needs a small but complete world: one evento edition, disciplines in
the three modalidades (M/F/X), personas with a known persisted gender, teams
and participaciones in both ACTIVE and RETIREDA state.

Everything is built here (no dependency on other modules' conftest fixtures)
so the same scenario can be reused from the root and the integration conftest.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EstadoParticipacionChoices,
    EtapaChoices,
    ModalidadChoices,
    ModoDisciplinasChoices,
    RolParticipanteChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    Disciplina,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaquetePrecio,
    Participacion,
    Promocion,
)
from modules.usuarios.domain.constants import GeneroChoices
from modules.usuarios.domain.models.persona import Persona


# ── Personas ──────────────────────────────────────────────────────────────────


@pytest.fixture
def persona_genero_masculino(db):
    """Persona with persisted gender M."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="90000001",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def persona_genero_femenino(db):
    """Persona with persisted gender F."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="90000002",
        genero=GeneroChoices.FEMENINO,
    )


@pytest.fixture
def persona_genero_masculino_2(db):
    """Second persona with persisted gender M."""
    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Rodríguez",
        tipo_documento="DNI",
        numero_documento="90000003",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def persona_genero_femenino_2(db):
    """Second persona with persisted gender F."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="López",
        tipo_documento="DNI",
        numero_documento="90000004",
        genero=GeneroChoices.FEMENINO,
    )


# ── Disciplines (the three modalidades) ───────────────────────────────────────


@pytest.fixture
def disciplina_modalidad_masculina(db):
    """Discipline with modality M."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="GENM",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_modalidad_femenina(db):
    """Discipline with modality F."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Femenino",
        sigla="GENF",
        modalidad=ModalidadChoices.FEMENINO,
        min_jugadores=7,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_modalidad_mixta(db):
    """Discipline with modality X."""
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="GENX",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def promocion_auditoria(db):
    """Promotion used by the audit scenarios."""
    return Promocion.objects.create(
        anio=2013,
        nombre="Junior auditoría",
        activa=True,
    )


# ── Scenario builders ─────────────────────────────────────────────────────────


def _crear_evento(nombre):
    return Evento.objects.create(
        nombre=nombre,
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


def _crear_paquete(evento, nombre):
    paquete = Paquete.objects.create(
        evento=evento,
        nombre=nombre,
        descripcion="Paquete construido para la auditoría de género",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=3,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


def _crear_equipos(inscripcion, disciplinas):
    equipos = {}
    for clave, disciplina in disciplinas.items():
        equipos[clave] = Equipo.objects.create(
            inscripcion=inscripcion,
            disciplina=disciplina,
            nombre=f"Equipo {clave} de auditoría",
            estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
        )
    return equipos


def _crear_participacion(inscripcion, equipo, disciplina, evento, persona, estado):
    inscripcion_persona, _ = InscripcionPersona.objects.get_or_create(
        inscripcion=inscripcion,
        persona=persona,
        defaults={"estado": EstadoInscripcionPersonaChoices.ACTIVO},
    )
    return Participacion.objects.create(
        inscripcion_persona=inscripcion_persona,
        equipo=equipo,
        disciplina=disciplina,
        evento=evento,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=estado,
    )


def _construir_escenario(
    nombre_evento,
    nombre_paquete,
    promocion,
    responsable,
    disciplinas,
    filas,
):
    """Build one edition with teams and participaciones.

    ``filas`` is a list of (clave, clave_disciplina, persona, estado) tuples.
    """
    evento = _crear_evento(nombre_evento)
    inscripcion = Inscripcion.objects.create(
        evento=evento,
        responsable=responsable,
        paquete=_crear_paquete(evento, nombre_paquete),
        promocion=promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    equipos = _crear_equipos(inscripcion, disciplinas)

    participaciones = {}
    for clave, clave_disciplina, persona, estado in filas:
        participaciones[clave] = _crear_participacion(
            inscripcion,
            equipos[clave_disciplina],
            disciplinas[clave_disciplina],
            evento,
            persona,
            estado,
        )

    return {
        "evento": evento,
        "inscripcion": inscripcion,
        "equipos": equipos,
        "disciplinas": disciplinas,
        "participaciones": participaciones,
    }


# ── Scenarios ─────────────────────────────────────────────────────────────────


@pytest.fixture
def escenario_auditoria_genero(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    disciplina_modalidad_femenina,
    disciplina_modalidad_mixta,
    persona_genero_masculino,
    persona_genero_femenino,
    persona_genero_masculino_2,
    persona_genero_femenino_2,
):
    """Edition with compatible AND incompatible ACTIVE participaciones.

    Compatible ACTIVE rows: M/M, F/F, M/X, F/X.
    Incompatible ACTIVE rows: F/M and M/F.
    Incompatible RETIREDA row: F/M (history — never reported as active).
    """
    disciplinas = {
        "M": disciplina_modalidad_masculina,
        "F": disciplina_modalidad_femenina,
        "X": disciplina_modalidad_mixta,
    }
    filas = [
        ("compatible_m_m", "M", persona_genero_masculino, EstadoParticipacionChoices.ACTIVA),
        ("compatible_f_f", "F", persona_genero_femenino, EstadoParticipacionChoices.ACTIVA),
        ("compatible_m_x", "X", persona_genero_masculino, EstadoParticipacionChoices.ACTIVA),
        ("compatible_f_x", "X", persona_genero_femenino, EstadoParticipacionChoices.ACTIVA),
        ("incompatible_f_m", "M", persona_genero_femenino, EstadoParticipacionChoices.ACTIVA),
        ("incompatible_m_f", "F", persona_genero_masculino_2, EstadoParticipacionChoices.ACTIVA),
        ("historial_f_m", "M", persona_genero_femenino_2, EstadoParticipacionChoices.RETIRADA),
    ]
    escenario = _construir_escenario(
        nombre_evento="Salesianos FEST Auditoría 2026",
        nombre_paquete="Paquete auditoría principal",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas=disciplinas,
        filas=filas,
    )
    escenario["personas"] = {
        "M": persona_genero_masculino,
        "F": persona_genero_femenino,
        "M2": persona_genero_masculino_2,
        "F2": persona_genero_femenino_2,
    }
    return escenario


@pytest.fixture
def escenario_auditoria_genero_limpio(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    disciplina_modalidad_femenina,
    disciplina_modalidad_mixta,
    persona_genero_masculino,
    persona_genero_femenino,
    persona_genero_masculino_2,
    persona_genero_femenino_2,
):
    """Edition with only compatible ACTIVE participaciones (clean scope)."""
    disciplinas = {
        "M": disciplina_modalidad_masculina,
        "F": disciplina_modalidad_femenina,
        "X": disciplina_modalidad_mixta,
    }
    filas = [
        ("compatible_m_m", "M", persona_genero_masculino, EstadoParticipacionChoices.ACTIVA),
        ("compatible_f_f", "F", persona_genero_femenino, EstadoParticipacionChoices.ACTIVA),
        ("compatible_m_x", "X", persona_genero_masculino_2, EstadoParticipacionChoices.ACTIVA),
        ("compatible_f_x", "X", persona_genero_femenino_2, EstadoParticipacionChoices.ACTIVA),
    ]
    escenario = _construir_escenario(
        nombre_evento="Salesianos FEST Auditoría Limpia 2026",
        nombre_paquete="Paquete auditoría limpia",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas=disciplinas,
        filas=filas,
    )
    escenario["personas"] = {
        "M": persona_genero_masculino,
        "F": persona_genero_femenino,
        "M2": persona_genero_masculino_2,
        "F2": persona_genero_femenino_2,
    }
    return escenario


@pytest.fixture
def escenario_auditoria_genero_otro_evento(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    disciplina_modalidad_femenina,
    disciplina_modalidad_mixta,
    persona_genero_masculino,
    persona_genero_femenino,
    persona_genero_masculino_2,
):
    """Second edition with exactly one incompatible ACTIVE participacion."""
    disciplinas = {
        "M": disciplina_modalidad_masculina,
        "F": disciplina_modalidad_femenina,
        "X": disciplina_modalidad_mixta,
    }
    filas = [
        ("compatible_m_m", "M", persona_genero_masculino, EstadoParticipacionChoices.ACTIVA),
        ("incompatible_m_f", "F", persona_genero_masculino_2, EstadoParticipacionChoices.ACTIVA),
    ]
    escenario = _construir_escenario(
        nombre_evento="Salesianos FEST Auditoría 2027",
        nombre_paquete="Paquete auditoría 2027",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas=disciplinas,
        filas=filas,
    )
    escenario["personas"] = {
        "M": persona_genero_masculino,
        "F": persona_genero_femenino,
        "M2": persona_genero_masculino_2,
    }
    return escenario


# ── Enforcement scenarios (Phase 1) ────────────────────────────────────────────
#
# The audit scenarios above build participaciones directly (read-only scope).
# The enforcement scenarios below are built for the WRITE paths: they need a
# paid cup (an ACTIVE AsignacionCupo) so the core service gets past the
# commercial gate and reaches the gender matrix.


@pytest.fixture
def compra_pagada_genero(db, persona_genero_masculino):
    """Paid purchase that backs the cupos of the enforcement scenarios."""
    return Compra.objects.create(
        responsable=persona_genero_masculino,
        descripcion="Compra pagada para la validación de género",
        referencia_externa="GEN-REF-1",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )


@pytest.fixture
def usuario_responsable_genero(db, persona_genero_masculino):
    """Authenticated user linked to the responsible of the enforcement edition."""
    User = get_user_model()
    return User.objects.create_user(
        username="responsable_genero",
        email="responsable_genero@example.com",
        password="testpass123",
        persona_fk=persona_genero_masculino,
    )


def _inscribir_con_cupo(inscripcion, persona, compra):
    """Register a persona in the inscripcion with an ACTIVE paid cup."""
    inscripcion_persona = InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        inscripcion_persona=inscripcion_persona,
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    return inscripcion_persona


@pytest.fixture
def escenario_genero_participacion(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    disciplina_modalidad_femenina,
    disciplina_modalidad_mixta,
    persona_genero_masculino,
    persona_genero_femenino,
    compra_pagada_genero,
):
    """Edition ready to drive the participation lifecycle.

    One inscription with a team per modality (M, F, X) and TWO registered
    personas with an ACTIVE paid cup:

    - `M` (masculine) — compatible with the M and X disciplines.
    - `F` (feminine)  — compatible with the F and X disciplines.

    So the same persona is compatible with one discipline and incompatible
    with the other, which is exactly what the matrix tests need.
    """
    evento = _crear_evento("Salesianos FEST Enforcement 2026")
    inscripcion = Inscripcion.objects.create(
        evento=evento,
        responsable=persona_genero_masculino,
        paquete=_crear_paquete(evento, "Paquete enforcement"),
        promocion=promocion_auditoria,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    disciplinas = {
        "M": disciplina_modalidad_masculina,
        "F": disciplina_modalidad_femenina,
        "X": disciplina_modalidad_mixta,
    }
    equipos = _crear_equipos(inscripcion, disciplinas)

    return {
        "evento": evento,
        "inscripcion": inscripcion,
        "equipos": equipos,
        "disciplinas": disciplinas,
        "personas": {
            "M": persona_genero_masculino,
            "F": persona_genero_femenino,
        },
        "inscripciones_persona": {
            "M": _inscribir_con_cupo(inscripcion, persona_genero_masculino, compra_pagada_genero),
            "F": _inscribir_con_cupo(inscripcion, persona_genero_femenino, compra_pagada_genero),
        },
    }


# ── Administration scenarios (Phase 2) ────────────────────────────────────────
#
# The admin guards protect the `Persona.genero` and `Disciplina.modalidad`
# edits. These scenarios cover the boundaries of the guard:
#
# - a RETIRED participacion never blocks an edit (it is history);
# - an ACTIVE participacion in a MIXED discipline never blocks an edit;
# - an ACTIVE participacion in ANY edition DOES block an edit.


@pytest.fixture
def escenario_admin_genero_sin_conflictos(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    disciplina_modalidad_mixta,
    persona_genero_masculino,
    persona_genero_femenino,
):
    """One edition with the two shapes that never block an admin edit.

    - `M` (masculine): only a RETIRED participacion in the M discipline.
    - `F` (feminine): only an ACTIVE participacion in the X (mixed) discipline.
    """
    disciplinas = {
        "M": disciplina_modalidad_masculina,
        "X": disciplina_modalidad_mixta,
    }
    filas = [
        ("historial_m", "M", persona_genero_masculino, EstadoParticipacionChoices.RETIRADA),
        ("activa_x", "X", persona_genero_femenino, EstadoParticipacionChoices.ACTIVA),
    ]
    escenario = _construir_escenario(
        nombre_evento="Salesianos FEST Admin Sin Conflictos 2026",
        nombre_paquete="Paquete admin sin conflictos",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas=disciplinas,
        filas=filas,
    )
    escenario["personas"] = {
        "M": persona_genero_masculino,
        "F": persona_genero_femenino,
    }
    return escenario


@pytest.fixture
def escenario_admin_genero_otra_edicion(
    db,
    promocion_auditoria,
    disciplina_modalidad_masculina,
    persona_genero_masculino,
):
    """Two editions where the blocking row only lives in the SECOND one.

    Edition 2026 holds a RETIRED participacion in the M discipline (history),
    edition 2027 holds the ACTIVE one. A gender change must be rejected
    because the guard looks at every edition, not only the current one.
    """
    primera = _construir_escenario(
        nombre_evento="Salesianos FEST Admin Edición 2026",
        nombre_paquete="Paquete admin edición 2026",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas={"M": disciplina_modalidad_masculina},
        filas=[
            (
                "historial_m",
                "M",
                persona_genero_masculino,
                EstadoParticipacionChoices.RETIRADA,
            ),
        ],
    )
    segunda = _construir_escenario(
        nombre_evento="Salesianos FEST Admin Edición 2027",
        nombre_paquete="Paquete admin edición 2027",
        promocion=promocion_auditoria,
        responsable=persona_genero_masculino,
        disciplinas={"M": disciplina_modalidad_masculina},
        filas=[
            (
                "activa_m",
                "M",
                persona_genero_masculino,
                EstadoParticipacionChoices.ACTIVA,
            ),
        ],
    )
    return {
        "ediciones": [primera, segunda],
        "personas": {"M": persona_genero_masculino},
        "disciplinas": {"M": disciplina_modalidad_masculina},
    }
