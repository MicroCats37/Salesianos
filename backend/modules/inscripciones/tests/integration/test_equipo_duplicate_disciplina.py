"""
Integration tests for duplicate discipline teams.

Tests that the backend no longer blocks creating multiple teams with the same
discipline for the same inscription — the DB constraint (uq_equipo_inscripcion_disciplina)
and service-level validar_equipo_duplicado check have been removed.

Note: The API-level validar_cantidad_disciplinas_paquete enforces distinct-discipline
requirements for FIJO/ELEGIBLE modes separately. This test exercises the service layer
directly to prove the duplicate-discipline constraint is gone.
"""
import pytest

from modules.inscripciones.domain.models import (
    Inscripcion,
    EquipoInscrito,
)
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.schemas.equipo_schemas import EquipoCreateData


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def inscripcion_for_equipos(
    db,
    evento_activo,
    paquete_basic,
    promocion_test,
    usuario_con_persona,
):
    """An inscription ready to receive equipos."""
    return Inscripcion.objects.create(
        evento=evento_activo,
        paquete=paquete_basic,
        promocion=promocion_test,
        responsable=usuario_con_persona.persona_fk,
        estado="RECIBIDA",
    )


# ── Tests ────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_dos_equipos_misma_disciplina_inscripcion_no_bloquea(
    inscripcion_for_equipos,
    disciplina_futbol,
):
    """
    GIVEN: An active inscription and a discipline
    WHEN:  Creating two EquipoInscrito records for the SAME inscription+disciplina
           (bypassing the API-level distinct-discipline validator)
    THEN:  Both equipos are created successfully
           (No UniqueConstraint violation, no validar_equipo_duplicado error)

    This test proves the DB constraint and service-level duplicate check are gone.
    """
    service = EquipoService()

    data1 = EquipoCreateData(
        inscripcion_id=str(inscripcion_for_equipos.id),
        disciplina_id=str(disciplina_futbol.id),
        nombre="Equipo Tigres FC",
    )
    data2 = EquipoCreateData(
        inscripcion_id=str(inscripcion_for_equipos.id),
        disciplina_id=str(disciplina_futbol.id),
        nombre="Equipo Leones FC",
    )

    equipo1 = service.crear(data1)
    assert str(equipo1.disciplina_id) == str(disciplina_futbol.id)
    assert equipo1.nombre == "Equipo Tigres FC"

    # This would raise EquipoDuplicadoError if the old validar_equipo_duplicado was active
    equipo2 = service.crear(data2)
    assert str(equipo2.disciplina_id) == str(disciplina_futbol.id)
    assert equipo2.nombre == "Equipo Leones FC"

    # Both equipos exist in DB
    equipos = list(EquipoInscrito.objects.filter(inscripcion=inscripcion_for_equipos))
    assert len(equipos) == 2
    assert {str(e.disciplina_id) for e in equipos} == {str(disciplina_futbol.id)}
