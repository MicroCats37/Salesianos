"""
Integration tests — ControlAccesoSelector and AceptacionInscripcionSelector
(read-only query surface of the salesianos_fest module).

Both tables had NO query surface before: the access log was only reachable
walking down from an acreditación, and the legal acceptances were not
readable at all. These selectors are what the operational administration
surface will read.
"""
from datetime import datetime, timedelta, timezone

import pytest

from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    ResultadoAccesoChoices,
    TipoAceptacionChoices,
)
from modules.salesianos_fest.domain.models import (
    AceptacionInscripcion,
    AcreditacionEvento,
    ControlAcceso,
    Inscripcion,
    InscripcionPersona,
)
from modules.salesianos_fest.domain.selectors import (
    AceptacionInscripcionSelector,
    ControlAccesoSelector,
)
from modules.usuarios.domain.models.persona import Persona

# `ControlAcceso.fecha_hora` is `auto_now_add`, so it cannot be set at creation
# time. The records get FIXED timestamps right after being created, so the
# ordering and the date-range filters are deterministic.
MOMENTO_PERMITIDO = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
MOMENTO_DENEGADO = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


def _fijar_fecha(control, momento):
    """Force the timestamp of an access record and refresh the instance."""
    ControlAcceso.objects.filter(id=control.id).update(fecha_hora=momento)
    control.refresh_from_db()
    return control


@pytest.fixture
def responsable(db):
    """Persona that owns the inscripcion."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def participante(db):
    """Persona that plays in the event."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def inscripcion(db, evento, responsable, paquete_reencuentro, promocion_junior):
    """Inscripcion of the active event."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=responsable,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.CONFIRMADA,
        observacion="",
    )


@pytest.fixture
def inscripcion_persona(db, inscripcion, participante):
    """Roster member of the inscripcion."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=participante,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def acreditacion(db, evento, participante):
    """Accreditation of the participant."""
    return AcreditacionEvento.objects.create(
        evento=evento,
        persona=participante,
        estado="ACTIVA",
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )


@pytest.fixture
def control_permitido(db, acreditacion):
    """Allowed access record."""
    control = ControlAcceso.objects.create(
        acreditacion=acreditacion,
        resultado=ResultadoAccesoChoices.PERMITIDO,
        punto_acceso="Puerta principal",
    )
    _fijar_fecha(control, MOMENTO_PERMITIDO)
    return control


@pytest.fixture
def control_denegado(db, acreditacion):
    """Denied access record."""
    control = ControlAcceso.objects.create(
        acreditacion=acreditacion,
        resultado=ResultadoAccesoChoices.DENEGADO,
        punto_acceso="Puerta lateral",
    )
    _fijar_fecha(control, MOMENTO_DENEGADO)
    return control


@pytest.fixture
def aceptacion(db, inscripcion_persona):
    """Legal acceptance of the roster member."""
    return AceptacionInscripcion.objects.create(
        inscripcion_persona=inscripcion_persona,
        tipo_aceptacion=TipoAceptacionChoices.BASES,
        documento_version="BASES-SF26-2026-09-06",
        actor_id=str(inscripcion_persona.persona_id),
    )


@pytest.fixture
def control_selector():
    """The access-log selector."""
    return ControlAccesoSelector()


@pytest.fixture
def aceptacion_selector():
    """The acceptance selector."""
    return AceptacionInscripcionSelector()


# ── ControlAccesoSelector ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_control_obtener_por_id(control_selector, control_permitido):
    """GIVEN: an existing access record WHEN: fetched by id THEN: it is returned."""
    assert control_selector.obtener_por_id(str(control_permitido.id)) == control_permitido


@pytest.mark.django_db
def test_control_obtener_por_id_desconocido(control_selector, db):
    """GIVEN: an unknown id WHEN: fetched THEN: None."""
    assert (
        control_selector.obtener_por_id("00000000-0000-0000-0000-000000000000")
        is None
    )


@pytest.mark.django_db
def test_control_listar_por_evento(control_selector, evento, control_permitido, control_denegado):
    """GIVEN: two access records of the event WHEN: listed THEN: both are returned."""
    assert control_selector.listar_por_evento(str(evento.id)).count() == 2


@pytest.mark.django_db
def test_control_listar_por_evento_ordena_del_mas_reciente(
    control_selector, evento, control_permitido, control_denegado
):
    """
    GIVEN: two access records
    WHEN:  listed
    THEN:  the most recent comes first.
    """
    registros = list(control_selector.listar_por_evento(str(evento.id)))

    assert registros[0].id == control_denegado.id


@pytest.mark.django_db
def test_control_listar_filtra_por_resultado(
    control_selector, evento, control_permitido, control_denegado
):
    """GIVEN: two access records WHEN: filtered by result THEN: only one matches."""
    registros = control_selector.listar_por_evento(
        str(evento.id), resultado=ResultadoAccesoChoices.PERMITIDO
    )

    assert list(registros) == [control_permitido]


@pytest.mark.django_db
def test_control_listar_filtra_por_punto_de_acceso(
    control_selector, evento, control_permitido, control_denegado
):
    """GIVEN: two access records WHEN: filtered by gate THEN: only one matches."""
    registros = control_selector.listar_por_evento(
        str(evento.id), punto_acceso="Puerta lateral"
    )

    assert list(registros) == [control_denegado]


@pytest.mark.django_db
def test_control_listar_filtra_por_rango_de_fechas(
    control_selector, evento, control_permitido, control_denegado
):
    """GIVEN: two access records WHEN: filtered by date range THEN: it narrows."""
    desde = MOMENTO_DENEGADO - timedelta(minutes=30)

    registros = control_selector.listar_por_evento(str(evento.id), desde=desde)

    assert list(registros) == [control_denegado]


@pytest.mark.django_db
def test_control_listar_filtra_por_fecha_limite(
    control_selector, evento, control_permitido, control_denegado
):
    """GIVEN: two access records WHEN: filtered by the upper bound THEN: it narrows."""
    hasta = MOMENTO_PERMITIDO + timedelta(minutes=30)

    registros = control_selector.listar_por_evento(str(evento.id), hasta=hasta)

    assert list(registros) == [control_permitido]


@pytest.mark.django_db
def test_control_listar_de_otro_evento_no_aparece(
    control_selector, evento, control_permitido, db
):
    """
    GIVEN: an access record of another event
    WHEN:  the event is listed
    THEN:  the record is NOT part of the result.
    """
    from datetime import date

    from modules.eventos.domain.models import Evento

    otro_evento = Evento.objects.create(
        nombre="Salesianos FEST 2025",
        fecha_inicio=date(2025, 11, 15),
        fecha_fin=date(2025, 11, 20),
        esta_activo=False,
    )
    otra_persona = Persona.objects.create(
        nombres="Pedro",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11223344",
        genero="M",
    )
    otra_acreditacion = AcreditacionEvento.objects.create(
        evento=otro_evento,
        persona=otra_persona,
        estado="ACTIVA",
        acceso_fiesta=False,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )
    ControlAcceso.objects.create(
        acreditacion=otra_acreditacion,
        resultado=ResultadoAccesoChoices.PERMITIDO,
    )

    assert control_selector.listar_por_evento(str(evento.id)).count() == 1


@pytest.mark.django_db
def test_control_contar_por_evento_devuelve_ambas_claves(
    control_selector, evento, control_permitido, control_denegado
):
    """
    GIVEN: one allowed and one denied access
    WHEN:  counted
    THEN:  both vocabulary keys are always present.
    """
    conteo = control_selector.contar_por_evento(str(evento.id))

    assert conteo == {
        ResultadoAccesoChoices.PERMITIDO: 1,
        ResultadoAccesoChoices.DENEGADO: 1,
    }


@pytest.mark.django_db
def test_control_contar_por_evento_sin_registros_devuelve_ceros(
    control_selector, evento, db
):
    """GIVEN: no access record WHEN: counted THEN: both counters are zero."""
    conteo = control_selector.contar_por_evento(str(evento.id))

    assert conteo[ResultadoAccesoChoices.PERMITIDO] == 0
    assert conteo[ResultadoAccesoChoices.DENEGADO] == 0


@pytest.mark.django_db
def test_control_ultimo_acceso(control_selector, evento, control_permitido, control_denegado):
    """GIVEN: two access records WHEN: the last one is asked THEN: the newest."""
    ultimo = control_selector.ultimo_acceso_por_evento(str(evento.id))

    assert ultimo == control_denegado.fecha_hora


@pytest.mark.django_db
def test_control_ultimo_acceso_sin_registros_devuelve_none(control_selector, evento, db):
    """GIVEN: no access record WHEN: the last one is asked THEN: None."""
    assert control_selector.ultimo_acceso_por_evento(str(evento.id)) is None


# ── AceptacionInscripcionSelector ─────────────────────────────────────────────


@pytest.mark.django_db
def test_aceptacion_obtener_por_id(aceptacion_selector, aceptacion):
    """GIVEN: an existing acceptance WHEN: fetched by id THEN: it is returned."""
    assert aceptacion_selector.obtener_por_id(str(aceptacion.id)) == aceptacion


@pytest.mark.django_db
def test_aceptacion_obtener_por_id_desconocido(aceptacion_selector, db):
    """GIVEN: an unknown id WHEN: fetched THEN: None."""
    assert (
        aceptacion_selector.obtener_por_id("00000000-0000-0000-0000-000000000000")
        is None
    )


@pytest.mark.django_db
def test_aceptacion_listar_por_inscripcion(
    aceptacion_selector, inscripcion, aceptacion
):
    """GIVEN: an acceptance of the inscripcion WHEN: listed THEN: it is returned."""
    assert list(aceptacion_selector.listar_por_inscripcion(str(inscripcion.id))) == [
        aceptacion
    ]


@pytest.mark.django_db
def test_aceptacion_listar_por_evento(aceptacion_selector, evento, aceptacion):
    """GIVEN: an acceptance of the event WHEN: listed THEN: it is returned."""
    assert list(aceptacion_selector.listar_por_evento(str(evento.id))) == [aceptacion]


@pytest.mark.django_db
def test_aceptacion_pendientes_excluye_a_quien_ya_acepto(
    aceptacion_selector, evento, inscripcion_persona, aceptacion
):
    """
    GIVEN: a roster member that ALREADY accepted
    WHEN:  the pending ones are listed
    THEN:  the member is NOT part of the result.
    """
    pendientes = list(aceptacion_selector.listar_pendientes_por_evento(str(evento.id)))

    assert inscripcion_persona not in pendientes


@pytest.mark.django_db
def test_aceptacion_pendientes_incluye_a_quien_no_acepto(
    aceptacion_selector, evento, inscripcion_persona
):
    """
    GIVEN: a roster member WITHOUT any acceptance
    WHEN:  the pending ones are listed
    THEN:  the member IS part of the result.
    """
    pendientes = list(aceptacion_selector.listar_pendientes_por_evento(str(evento.id)))

    assert inscripcion_persona in pendientes


@pytest.mark.django_db
def test_aceptacion_pendientes_ignora_a_los_retirados(
    aceptacion_selector, evento, inscripcion_persona
):
    """
    GIVEN: a roster member that was RETIRED and never accepted
    WHEN:  the pending ones are listed
    THEN:  a retired member is not pending anymore.
    """
    inscripcion_persona.estado = EstadoInscripcionPersonaChoices.RETIRADO
    inscripcion_persona.save(update_fields=["estado"])

    pendientes = list(aceptacion_selector.listar_pendientes_por_evento(str(evento.id)))

    assert inscripcion_persona not in pendientes
