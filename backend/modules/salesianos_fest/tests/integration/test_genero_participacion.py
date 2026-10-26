"""
Integration tests for the discipline/gender participation compatibility change.

Phase 0 covers the read-only audit command `auditar_genero_disciplinas`:

- reports every incompatible ACTIVE participacion
- never reports RETIREDA history
- scopes the report to one evento/edition with `--evento-id`
- is deterministic and never writes
- exits 0 when the audited scope is clean, 1 when it has violations or the
  requested scope is invalid

Phase 1 covers the shared compatibility matrix, the typed 409 conflict and the
active-lifecycle enforcement:

- the matrix accepts M/M, M/X, F/F, F/X and rejects M/F, F/M (fail closed)
- the matrix has a single owner (the domain predicate)
- an ACTIVE participacion can only be created, moved or reactivated when the
  persisted gender is compatible with the discipline modality
- retirement stays allowed and a rejected action mutates nothing
- the public conflict is a 409 with the stable code `GENERO_NO_PERMITIDO` and
  no identifiers
- `Participacion.clean()` is the safety net for the paths that bypass the
  core service

Phase 2 covers the Django Admin guards:

- a `Persona.genero` edit that would break an ACTIVE participacion is
  rejected, in ANY edition
- a `Disciplina.modalidad` edit that would break an ACTIVE participacion is
  rejected, in ANY edition
- retired history never blocks an edit and a no-op save is always allowed
- the rejected edit changes nothing in the database
- the conflict is reported exactly once (admin + model clean never duplicate)

Phase 3 covers the ADVISORY verdict of the participant selector:

- a candidate whose persisted gender is not accepted by the modality of the
  target discipline is NOT assignable and reports the UI-safe reason
- a MIXED discipline (X) accepts every candidate
- the reason is UI-safe: no identifier, UUID or technical detail
- the selector reuses the shared predicate — it never keeps a private matrix
"""
import io
import json
from uuid import UUID

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.management import load_command_class
from django.test import Client
from django.test import override_settings
from django.urls import reverse
from ninja_jwt.tokens import AccessToken

from modules.salesianos_fest.domain.constants import (
    EstadoParticipacionChoices,
    ModalidadChoices,
    MOTIVO_GENERO_NO_COMPATIBLE,
    RolParticipanteChoices,
)
from modules.salesianos_fest.domain.exceptions import GeneroNoPermitidoError
from modules.salesianos_fest.domain.models import Disciplina, Participacion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    ParticipacionUpdateData,
)
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.services.core.participacion_service import (
    ParticipacionCoreService,
)
from modules.salesianos_fest.domain.validators import (
    es_genero_compatible_con_modalidad,
)
from modules.salesianos_fest.forms import (
    DisciplinaAdminForm,
    ParticipacionAdminForm,
)
from modules.usuarios.domain.constants import GeneroChoices
from modules.usuarios.domain.models.persona import Persona
from modules.usuarios.forms import PersonaAdminForm


COMANDO = "auditar_genero_disciplinas"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _ejecutar(**opciones):
    """Run the audit command. Returns (stdout, CommandError or None)."""
    stdout = io.StringIO()
    error = None
    try:
        call_command(COMANDO, stdout=stdout, **opciones)
    except CommandError as exc:
        error = exc
    return stdout.getvalue(), error


def _violaciones(stdout):
    return [line for line in stdout.splitlines() if line.startswith("VIOLATION|")]


def _resumen(stdout):
    for line in stdout.splitlines():
        if line.startswith("SUMMARY|"):
            return line
    return None


def _campos(line):
    partes = line.split("|")
    assert partes[0] == "VIOLATION"
    assert len(partes) == 7
    return {
        "evento_id": partes[1],
        "participacion_id": partes[2],
        "persona_id": partes[3],
        "genero": partes[4],
        "disciplina_id": partes[5],
        "modalidad": partes[6],
    }


def _snapshot():
    """Snapshot of everything the audit must not touch."""
    participaciones = sorted(
        (
            str(p.id),
            str(p.evento_id),
            str(p.disciplina_id),
            str(p.persona_id),
            str(p.equipo_id),
            str(p.inscripcion_persona_id),
            p.estado,
            p.rol,
            p.talla_camiseta,
            p.notas,
            p.updated_at.isoformat(),
        )
        for p in Participacion.objects.all()
    )
    personas = sorted(
        (str(p.id), p.genero, p.updated_at.isoformat())
        for p in Persona.objects.all()
    )
    disciplinas = sorted(
        (str(d.id), d.modalidad, d.updated_at.isoformat())
        for d in Disciplina.objects.all()
    )
    return participaciones, personas, disciplinas


# ── Audit: incompatible ACTIVE rows ───────────────────────────────────────────


@pytest.mark.django_db
def test_audit_reporta_solo_participaciones_activas_incompatibles(
    escenario_auditoria_genero,
):
    """
    GIVEN: an edition with compatible and incompatible ACTIVE participaciones
    WHEN:  the audit runs
    THEN:  every incompatible ACTIVE row is reported
    AND:   the summary counts the scanned rows and the violations
    """
    stdout, error = _ejecutar()

    assert error is not None, "the audit must fail when there are violations"
    assert error.returncode == 1

    participaciones = escenario_auditoria_genero["participaciones"]
    esperadas = {
        str(participaciones["incompatible_f_m"].id),
        str(participaciones["incompatible_m_f"].id),
    }

    reportadas = {_campos(line)["participacion_id"] for line in _violaciones(stdout)}

    assert reportadas == esperadas
    assert _resumen(stdout) == "SUMMARY|scanned=6|violations=2"


@pytest.mark.django_db
def test_audit_excluye_el_historial_retirado(escenario_auditoria_genero):
    """
    GIVEN: an incompatible participacion in state R (retired)
    WHEN:  the audit runs
    THEN:  it is NOT reported as an active violation
    """
    participaciones = escenario_auditoria_genero["participaciones"]
    retirada_id = str(participaciones["historial_f_m"].id)

    stdout, _ = _ejecutar()

    assert retirada_id not in {
        _campos(line)["participacion_id"] for line in _violaciones(stdout)
    }


@pytest.mark.django_db
def test_audit_no_reporta_filas_compatibles(escenario_auditoria_genero):
    """
    GIVEN: compatible ACTIVE participaciones (M/M, F/F, M/X, F/X)
    WHEN:  the audit runs
    THEN:  none of them is reported
    """
    participaciones = escenario_auditoria_genero["participaciones"]

    stdout, _ = _ejecutar()

    reportadas = {_campos(line)["participacion_id"] for line in _violaciones(stdout)}
    for clave in ("compatible_m_m", "compatible_f_f", "compatible_m_x", "compatible_f_x"):
        assert str(participaciones[clave].id) not in reportadas


@pytest.mark.django_db
def test_audit_reporta_los_campos_de_cada_violacion(escenario_auditoria_genero):
    """
    GIVEN: an incompatible ACTIVE participacion (persona F in a M discipline)
    WHEN:  the audit runs
    THEN:  the row reports evento, participacion, persona, genero, disciplina
           and modalidad
    """
    participaciones = escenario_auditoria_genero["participaciones"]
    victima = participaciones["incompatible_f_m"]

    stdout, _ = _ejecutar()

    lineas = [
        _campos(line)
        for line in _violaciones(stdout)
        if _campos(line)["participacion_id"] == str(victima.id)
    ]
    assert len(lineas) == 1
    campos = lineas[0]
    assert campos["evento_id"] == str(victima.evento_id)
    assert campos["persona_id"] == str(victima.persona_id)
    assert campos["genero"] == "F"
    assert campos["disciplina_id"] == str(victima.disciplina_id)
    assert campos["modalidad"] == "M"


# ── Audit: determinism ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_audit_es_determinista_entre_ejecuciones(escenario_auditoria_genero):
    """
    GIVEN: the same persisted data
    WHEN:  the audit runs twice
    THEN:  both runs produce exactly the same output
    """
    primera, _ = _ejecutar()
    segunda, _ = _ejecutar()

    assert primera == segunda


@pytest.mark.django_db
def test_audit_ordena_las_violaciones_por_evento_y_participacion(
    escenario_auditoria_genero,
):
    """
    GIVEN: several incompatible ACTIVE participaciones
    WHEN:  the audit runs
    THEN:  the rows are ordered by (evento_id, participacion_id)
    """
    stdout, _ = _ejecutar()

    claves = [
        (_campos(line)["evento_id"], _campos(line)["participacion_id"])
        for line in _violaciones(stdout)
    ]

    assert claves == sorted(claves)


# ── Audit: event scope ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_audit_filtra_por_evento_id(
    escenario_auditoria_genero,
    escenario_auditoria_genero_otro_evento,
):
    """
    GIVEN: two editions, one with two violations and one with a single violation
    WHEN:  the audit runs scoped to one edition
    THEN:  only the rows of that edition are reported
    AND:   the summary counts only the scanned rows of that edition
    """
    evento_objetivo = escenario_auditoria_genero["evento"]

    stdout, error = _ejecutar(evento_id=str(evento_objetivo.id))

    assert error is not None
    assert error.returncode == 1

    evento_otro = escenario_auditoria_genero_otro_evento["evento"]
    reportadas = {_campos(line)["participacion_id"] for line in _violaciones(stdout)}

    assert len(reportadas) == 2
    assert all(
        _campos(line)["evento_id"] == str(evento_objetivo.id)
        for line in _violaciones(stdout)
    )
    assert not any(
        _campos(line)["evento_id"] == str(evento_otro.id)
        for line in _violaciones(stdout)
    )
    assert _resumen(stdout) == "SUMMARY|scanned=6|violations=2"


@pytest.mark.django_db
def test_audit_sin_scope_audita_todas_las_ediciones(
    escenario_auditoria_genero,
    escenario_auditoria_genero_otro_evento,
):
    """
    GIVEN: two editions with violations
    WHEN:  the audit runs without a scope
    THEN:  the violations of every edition are reported
    """
    stdout, error = _ejecutar()

    assert error is not None
    assert len(_violaciones(stdout)) == 3
    assert _resumen(stdout) == "SUMMARY|scanned=8|violations=3"


@pytest.mark.django_db
def test_audit_con_evento_inexistente_falla(escenario_auditoria_genero):
    """
    GIVEN: an evento id that does not exist
    WHEN:  the audit runs with that scope
    THEN:  it fails with an invalid scope error
    """
    stdout, error = _ejecutar(evento_id=str(UUID(int=0)))

    assert error is not None
    assert error.returncode == 1
    assert "evento" in str(error).lower()
    assert _violaciones(stdout) == []


@pytest.mark.django_db
def test_audit_con_uuid_invalido_falla(escenario_auditoria_genero):
    """
    GIVEN: an evento id that is not a UUID
    WHEN:  the audit runs with that scope
    THEN:  it fails with an invalid scope error
    """
    stdout, error = _ejecutar(evento_id="no-es-un-uuid")

    assert error is not None
    assert error.returncode == 1
    assert _violaciones(stdout) == []


# ── Audit: zero / nonzero behavior ───────────────────────────────────────────


@pytest.mark.django_db
def test_audit_sin_violaciones_no_falla(escenario_auditoria_genero_limpio):
    """
    GIVEN: an edition with only compatible ACTIVE participaciones
    WHEN:  the audit runs
    THEN:  it succeeds (exit code 0) and reports no violations
    """
    stdout, error = _ejecutar()

    assert error is None
    assert _violaciones(stdout) == []
    assert _resumen(stdout) == "SUMMARY|scanned=4|violations=0"


@pytest.mark.django_db(transaction=True)
def test_audit_termina_con_codigo_de_salida_uno_ante_violaciones(
    escenario_auditoria_genero,
):
    """
    GIVEN: an edition with incompatible ACTIVE participaciones
    WHEN:  the command runs as a management command
    THEN:  the process exits with a non-zero code (1)
    """
    comando = load_command_class("modules.salesianos_fest", COMANDO)

    with pytest.raises(SystemExit) as exc_info:
        comando.run_from_argv(["manage.py", COMANDO, "--skip-checks"])

    assert exc_info.value.code == 1


@pytest.mark.django_db(transaction=True)
def test_audit_termina_con_codigo_de_salida_cero_sin_violaciones(
    escenario_auditoria_genero_limpio,
):
    """
    GIVEN: an edition with only compatible ACTIVE participaciones
    WHEN:  the command runs as a management command
    THEN:  the process exits with code 0
    """
    comando = load_command_class("modules.salesianos_fest", COMANDO)

    comando.run_from_argv(["manage.py", COMANDO, "--skip-checks"])


# ── Audit: read-only ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_audit_no_modifica_ningun_registro(escenario_auditoria_genero):
    """
    GIVEN: persisted participaciones, personas and disciplines
    WHEN:  the audit runs
    THEN:  no record is created, updated or deleted
    """
    antes = _snapshot()

    _ejecutar()

    assert _snapshot() == antes


@pytest.mark.django_db
def test_audit_sin_violaciones_tampoco_modifica_registros(
    escenario_auditoria_genero_limpio,
):
    """
    GIVEN: an edition with only compatible ACTIVE participaciones
    WHEN:  the audit runs
    THEN:  no record is created, updated or deleted
    """
    antes = _snapshot()

    _ejecutar()

    assert _snapshot() == antes


# ── Phase 1: the shared compatibility matrix ──────────────────────────────────


@pytest.mark.parametrize(
    "genero,modalidad",
    [
        ("M", "M"),
        ("M", "X"),
        ("F", "F"),
        ("F", "X"),
    ],
)
def test_matrix_acepta_los_pares_permitidos(genero, modalidad):
    """
    GIVEN: an allowed pair (M/M, M/X, F/F, F/X)
    WHEN:  compatibility is evaluated
    THEN:  it is accepted
    """
    assert es_genero_compatible_con_modalidad(genero, modalidad) is True


@pytest.mark.parametrize(
    "genero,modalidad",
    [
        ("M", "F"),
        ("F", "M"),
    ],
)
def test_matrix_rechaza_los_pares_prohibidos(genero, modalidad):
    """
    GIVEN: a forbidden pair (M/F, F/M)
    WHEN:  compatibility is evaluated
    THEN:  it is rejected
    """
    assert es_genero_compatible_con_modalidad(genero, modalidad) is False


@pytest.mark.parametrize(
    "genero,modalidad",
    [
        ("X", "X"),  # unknown gender
        ("", "X"),  # empty gender
        (None, "X"),  # missing gender
        ("M", ""),  # unknown modality
        ("M", None),  # missing modality
        ("M", "Z"),  # unknown modality code
    ],
)
def test_matrix_falla_cerrado_con_pares_desconocidos(genero, modalidad):
    """
    GIVEN: a pair outside the allow-list
    WHEN:  compatibility is evaluated
    THEN:  it is rejected (the rule fails closed)
    """
    assert es_genero_compatible_con_modalidad(genero, modalidad) is False


def test_matrix_falla_cerrado_con_valores_no_comparables():
    """
    GIVEN: values that cannot even be compared with the allow-list
    WHEN:  compatibility is evaluated
    THEN:  it is rejected instead of raising
    """
    assert es_genero_compatible_con_modalidad(["M"], "M") is False
    assert es_genero_compatible_con_modalidad("M", ["X"]) is False


def test_matrix_tiene_un_unico_dueno_en_el_dominio():
    """
    GIVEN: the audit command and the shared domain predicate
    WHEN:  the command is inspected
    THEN:  it IMPORTS the predicate instead of keeping a private copy
    AND:   both call the very same function object
    """
    import inspect

    from modules.salesianos_fest.management.commands import (
        auditar_genero_disciplinas as comando,
    )

    assert (
        comando.es_genero_compatible_con_modalidad
        is es_genero_compatible_con_modalidad
    )
    assert "def es_genero_compatible_con_modalidad" not in inspect.getsource(comando)


# ── Phase 1: active lifecycle enforcement ────────────────────────────────────


def _crear_participacion(inscripcion_persona, equipo):
    """Create an ACTIVE participacion through the core service."""
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
        ParticipacionCreateData,
    )

    data = ParticipacionCreateData(
        inscripcion_persona_id=str(inscripcion_persona.id),
        equipo_id=str(equipo.id),
        rol="J",
    )
    return ParticipacionCoreService().crear(data)


def _crear_participacion_directa(escenario, clave_persona, clave_disciplina, estado):
    """Persist a participacion bypassing the core service (legacy data shape)."""
    return Participacion.objects.create(
        inscripcion_persona=escenario["inscripciones_persona"][clave_persona],
        equipo=escenario["equipos"][clave_disciplina],
        evento=escenario["evento"],
        disciplina=escenario["disciplinas"][clave_disciplina],
        persona=escenario["personas"][clave_persona],
        rol=RolParticipanteChoices.JUGADOR,
        estado=estado,
    )


@pytest.mark.django_db
def test_lifecycle_crea_una_participacion_activa_compatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a masculine persona with an active cup and an M discipline
    WHEN:  the core service creates an ACTIVE participacion
    THEN:  the participacion is created
    """
    escenario = escenario_genero_participacion

    p = _crear_participacion(
        escenario["inscripciones_persona"]["M"],
        escenario["equipos"]["M"],
    )

    assert p.estado == EstadoParticipacionChoices.ACTIVA
    assert str(p.disciplina_id) == str(escenario["disciplinas"]["M"].id)
    assert str(p.persona_id) == str(escenario["personas"]["M"].id)


@pytest.mark.django_db
def test_lifecycle_rechaza_crear_una_participacion_activa_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a feminine persona and a masculine-only discipline
    WHEN:  the core service tries to create an ACTIVE participacion
    THEN:  GeneroNoPermitidoError is raised
    AND:   no participacion row is created
    """
    escenario = escenario_genero_participacion

    with pytest.raises(GeneroNoPermitidoError):
        _crear_participacion(
            escenario["inscripciones_persona"]["F"],
            escenario["equipos"]["M"],
        )

    assert not Participacion.objects.exists()


@pytest.mark.django_db
def test_lifecycle_acepta_cualquier_genero_en_un_equipo_mixto(
    escenario_genero_participacion,
):
    """
    GIVEN: a mixed (X) discipline
    WHEN:  a feminine persona is added to it
    THEN:  the participacion is created (X accepts any gender)
    """
    escenario = escenario_genero_participacion

    p = _crear_participacion(
        escenario["inscripciones_persona"]["F"],
        escenario["equipos"]["X"],
    )

    assert p.estado == EstadoParticipacionChoices.ACTIVA


@pytest.mark.django_db
def test_lifecycle_rechaza_mover_a_una_disciplina_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion of a masculine persona in the M discipline
    WHEN:  it is moved to a feminine discipline
    THEN:  GeneroNoPermitidoError is raised
    AND:   the original assignment is preserved
    """
    escenario = escenario_genero_participacion
    p = _crear_participacion(
        escenario["inscripciones_persona"]["M"],
        escenario["equipos"]["M"],
    )
    equipo_origen = str(p.equipo_id)
    disciplina_origen = str(p.disciplina_id)

    with pytest.raises(GeneroNoPermitidoError):
        ParticipacionCoreService().mover(p, str(escenario["equipos"]["F"].id))

    p.refresh_from_db()
    assert str(p.equipo_id) == equipo_origen
    assert str(p.disciplina_id) == disciplina_origen
    assert p.estado == EstadoParticipacionChoices.ACTIVA


@pytest.mark.django_db
def test_lifecycle_permite_mover_a_una_disciplina_compatible(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion of a masculine persona in the M discipline
    WHEN:  it is moved to a mixed (X) discipline
    THEN:  the move succeeds and the discipline is re-synced
    """
    escenario = escenario_genero_participacion
    p = _crear_participacion(
        escenario["inscripciones_persona"]["M"],
        escenario["equipos"]["M"],
    )

    movida = ParticipacionCoreService().mover(p, str(escenario["equipos"]["X"].id))

    assert str(movida.equipo_id) == str(escenario["equipos"]["X"].id)
    assert str(movida.disciplina_id) == str(escenario["disciplinas"]["X"].id)
    assert movida.estado == EstadoParticipacionChoices.ACTIVA


@pytest.mark.django_db
def test_lifecycle_rechaza_reactivar_una_participacion_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a RETIREDA participacion whose gender conflicts with the discipline
    WHEN:  it is reactivated (R -> A)
    THEN:  GeneroNoPermitidoError is raised
    AND:   the row stays RETIREDA
    """
    escenario = escenario_genero_participacion
    retirada = _crear_participacion_directa(
        escenario, "F", "M", EstadoParticipacionChoices.RETIRADA
    )

    with pytest.raises(GeneroNoPermitidoError):
        ParticipacionCoreService().actualizar(
            retirada,
            ParticipacionUpdateData(estado=EstadoParticipacionChoices.ACTIVA),
        )

    retirada.refresh_from_db()
    assert retirada.estado == EstadoParticipacionChoices.RETIRADA


@pytest.mark.django_db
def test_lifecycle_permite_reactivar_una_participacion_compatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a RETIREDA participacion of a feminine persona in the F discipline
    WHEN:  it is reactivated (R -> A)
    THEN:  the reactivation succeeds
    """
    escenario = escenario_genero_participacion
    retirada = _crear_participacion_directa(
        escenario, "F", "F", EstadoParticipacionChoices.RETIRADA
    )

    reactivada = ParticipacionCoreService().actualizar(
        retirada,
        ParticipacionUpdateData(estado=EstadoParticipacionChoices.ACTIVA),
    )

    assert reactivada.estado == EstadoParticipacionChoices.ACTIVA


@pytest.mark.django_db
def test_lifecycle_permite_retirar_una_participacion_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion that violates the matrix (legacy data)
    WHEN:  it is retired
    THEN:  the transition succeeds — retirement is never blocked
    """
    escenario = escenario_genero_participacion
    activa = _crear_participacion_directa(
        escenario, "F", "M", EstadoParticipacionChoices.ACTIVA
    )

    retirada = ParticipacionCoreService().retirer(activa)

    assert retirada.estado == EstadoParticipacionChoices.RETIRADA


@pytest.mark.django_db
def test_lifecycle_no_exige_el_genero_en_una_edicion_que_no_cambia_el_estado(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion that violates the matrix (legacy data)
    WHEN:  a field that is not the state is updated
    THEN:  the update succeeds — only the R -> A transition is gated
    """
    escenario = escenario_genero_participacion
    activa = _crear_participacion_directa(
        escenario, "F", "M", EstadoParticipacionChoices.ACTIVA
    )

    actualizada = ParticipacionCoreService().actualizar(
        activa,
        ParticipacionUpdateData(notas="Ajuste de notas"),
    )

    assert actualizada.notas == "Ajuste de notas"
    assert actualizada.estado == EstadoParticipacionChoices.ACTIVA


# ── Phase 1: the stable public conflict ──────────────────────────────────────


def test_conflict_el_error_de_genero_es_un_409_con_codigo_estable():
    """
    GIVEN: the typed domain error
    WHEN:  it is built
    THEN:  it is a 409 conflict with the stable code GENERO_NO_PERMITIDO
    """
    from core.exceptions import ConflictError

    error = GeneroNoPermitidoError()

    assert error.code == "GENERO_NO_PERMITIDO"
    assert error.status_code == 409
    assert isinstance(error, ConflictError)


def test_conflict_el_mensaje_publico_no_expone_identificadores():
    """
    GIVEN: the public error catalog
    WHEN:  the GENERO_NO_PERMITIDO message is read
    THEN:  it exposes no identifier, UUID, number or technical detail
    """
    from core.exceptions import PUBLIC_ERROR_MESSAGES

    mensaje = PUBLIC_ERROR_MESSAGES["GENERO_NO_PERMITIDO"]

    assert mensaje
    assert not any(caracter.isdigit() for caracter in mensaje)
    for tecnico in ("Traceback", "Exception", "SELECT", "uuid", "UUID", "None"):
        assert tecnico not in mensaje


@pytest.mark.django_db(transaction=True)
def test_conflict_la_api_devuelve_409_con_el_codigo_estable(
    api_client,
    escenario_genero_participacion,
    usuario_responsable_genero,
):
    """
    GIVEN: the responsible of an inscription over HTTP
    WHEN:  it tries to create an incompatible ACTIVE participacion
    THEN:  the response is 409 with code GENERO_NO_PERMITIDO
    AND:   the body exposes no identifiers
    AND:   no participacion row is created
    """
    escenario = escenario_genero_participacion
    inscripcion_persona = escenario["inscripciones_persona"]["F"]
    equipo = escenario["equipos"]["M"]

    token = AccessToken.for_user(usuario_responsable_genero)
    response = api_client.post(
        "/api/participaciones/",
        data=json.dumps(
            {
                "inscripcion_persona_id": str(inscripcion_persona.id),
                "equipo_id": str(equipo.id),
                "rol": "J",
            }
        ),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "GENERO_NO_PERMITIDO"

    cuerpo = json.dumps(body)
    assert str(inscripcion_persona.id) not in cuerpo
    assert str(equipo.id) not in cuerpo

    assert not Participacion.objects.exists()


# ── Phase 1: the model safety net ────────────────────────────────────────────


def _participacion_pendiente(escenario, clave_persona, clave_disciplina, estado):
    return Participacion(
        inscripcion_persona=escenario["inscripciones_persona"][clave_persona],
        equipo=escenario["equipos"][clave_disciplina],
        evento=escenario["evento"],
        disciplina=escenario["disciplinas"][clave_disciplina],
        persona=escenario["personas"][clave_persona],
        rol=RolParticipanteChoices.JUGADOR,
        estado=estado,
    )


@pytest.mark.django_db
def test_model_clean_rechaza_una_participacion_activa_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion whose gender conflicts with the discipline
    WHEN:  the model is validated
    THEN:  a Django ValidationError is raised
    """
    from django.core.exceptions import ValidationError

    p = _participacion_pendiente(
        escenario_genero_participacion,
        "F",
        "M",
        EstadoParticipacionChoices.ACTIVA,
    )

    with pytest.raises(ValidationError):
        p.full_clean()


@pytest.mark.django_db
def test_model_clean_acepta_una_participacion_activa_compatible(
    escenario_genero_participacion,
):
    """
    GIVEN: an ACTIVE participacion whose gender matches the discipline
    WHEN:  the model is validated
    THEN:  no error is raised
    """
    p = _participacion_pendiente(
        escenario_genero_participacion,
        "M",
        "M",
        EstadoParticipacionChoices.ACTIVA,
    )

    p.full_clean()


@pytest.mark.django_db
def test_model_clean_permite_el_historial_retirado_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a RETIREDA participacion whose gender conflicts with the discipline
    WHEN:  the model is validated
    THEN:  no error is raised — the incompatible history stays remediable
    """
    p = _participacion_pendiente(
        escenario_genero_participacion,
        "F",
        "M",
        EstadoParticipacionChoices.RETIRADA,
    )

    p.full_clean()


# ── Phase 2: Django Admin guards ─────────────────────────────────────────────
#
# The admin protects the `Persona.genero` and `Disciplina.modalidad` edits: an
# edit that would leave an ACTIVE participacion incompatible is rejected with
# a field error, in ANY edition. Retired history never blocks an edit, a no-op
# save is always allowed, and the rules are the SAME shared predicate used by
# the audit and by the lifecycle enforcement.


def _datos_persona(persona, **cambios):
    """Admin POST payload of the Persona change form."""
    datos = {
        "tipo_documento": persona.tipo_documento,
        "numero_documento": persona.numero_documento,
        "nombres": persona.nombres,
        "apellidos": persona.apellidos,
        "genero": persona.genero,
        "telefono": persona.telefono or "",
        "whatsapp": persona.whatsapp or "",
        "contacto_emergencia_nombre": persona.contacto_emergencia_nombre or "",
        "contacto_emergencia_telefono": persona.contacto_emergencia_telefono or "",
        "aseguradora_nombre": persona.aseguradora_nombre or "",
        "aseguradora_numero_poliza": persona.aseguradora_numero_poliza or "",
    }
    datos.update(cambios)
    return datos


def _datos_disciplina(disciplina, **cambios):
    """Admin POST payload of the Disciplina change form."""
    datos = {
        "nombre": disciplina.nombre,
        "sigla": disciplina.sigla,
        "modalidad": disciplina.modalidad,
        "min_jugadores": disciplina.min_jugadores,
        "max_jugadores": disciplina.max_jugadores,
        "esta_activa": disciplina.esta_activa,
    }
    datos.update(cambios)
    return datos


def _datos_participacion(escenario, clave_persona, clave_disciplina, estado):
    """Admin POST payload of the Participacion change form."""
    return {
        "inscripcion_persona": str(escenario["inscripciones_persona"][clave_persona].id),
        "equipo": str(escenario["equipos"][clave_disciplina].id),
        "evento": str(escenario["evento"].id),
        "disciplina": str(escenario["disciplinas"][clave_disciplina].id),
        "persona": str(escenario["personas"][clave_persona].id),
        "rol": RolParticipanteChoices.JUGADOR,
        "talla_camiseta": "",
        "notas": "",
        "estado": estado,
    }


def _mensajes_de_error(form):
    """Every error message of a bound form, flattened."""
    return [mensaje for errores in form.errors.values() for mensaje in errores]


# ── Phase 2: the Persona.genero guard ─────────────────────────────────────────


@pytest.mark.django_db
def test_admin_rechaza_cambiar_el_genero_con_una_participacion_activa_incompatible(
    escenario_auditoria_genero,
):
    """
    GIVEN: a feminine persona with an ACTIVE participacion in a masculine discipline
    WHEN:  an administrator saves a masculine gender
    THEN:  the form is rejected with a field error on `genero`
    AND:   the original gender is preserved in the database
    """
    persona = escenario_auditoria_genero["personas"]["F"]

    form = PersonaAdminForm(
        data=_datos_persona(persona, genero=GeneroChoices.MASCULINO),
        instance=persona,
    )

    assert form.is_valid() is False
    assert "genero" in form.errors
    assert len(_mensajes_de_error(form)) == 1

    persona.refresh_from_db()
    assert persona.genero == GeneroChoices.FEMENINO


@pytest.mark.django_db
def test_admin_el_error_de_genero_no_expone_identificadores(
    escenario_auditoria_genero,
):
    """
    GIVEN: the admin guard of the `genero` field
    WHEN:  the conflict is reported
    THEN:  the message names the rule and never a record identifier
    """
    persona = escenario_auditoria_genero["personas"]["F"]

    form = PersonaAdminForm(
        data=_datos_persona(persona, genero=GeneroChoices.MASCULINO),
        instance=persona,
    )
    form.is_valid()

    mensaje = form.errors["genero"][0]
    assert str(persona.id) not in mensaje
    assert persona.numero_documento not in mensaje
    assert "Traceback" not in mensaje
    assert "ValidationError" not in mensaje


@pytest.mark.django_db
def test_admin_rechaza_cambiar_el_genero_con_una_participacion_activa_de_otra_edicion(
    escenario_admin_genero_otra_edicion,
):
    """
    GIVEN: a masculine persona whose only ACTIVE participacion lives in ANOTHER edition
    WHEN:  an administrator saves a feminine gender
    THEN:  the form is rejected — the guard looks at every edition
    """
    persona = escenario_admin_genero_otra_edicion["personas"]["M"]

    form = PersonaAdminForm(
        data=_datos_persona(persona, genero=GeneroChoices.FEMENINO),
        instance=persona,
    )

    assert form.is_valid() is False
    assert "genero" in form.errors

    persona.refresh_from_db()
    assert persona.genero == GeneroChoices.MASCULINO


@pytest.mark.django_db
def test_admin_permite_cambiar_el_genero_cuando_solo_hay_historial_retirado(
    escenario_admin_genero_sin_conflictos,
):
    """
    GIVEN: a masculine persona whose only participacion in the M discipline is RETIRED
    WHEN:  an administrator saves a feminine gender
    THEN:  the form is accepted — the incompatible history never blocks an edit
    """
    persona = escenario_admin_genero_sin_conflictos["personas"]["M"]

    form = PersonaAdminForm(
        data=_datos_persona(persona, genero=GeneroChoices.FEMENINO),
        instance=persona,
    )

    assert form.is_valid() is True
    assert form.errors == {}


@pytest.mark.django_db
def test_admin_permite_cambiar_el_genero_con_una_participacion_activa_mixta(
    escenario_admin_genero_sin_conflictos,
):
    """
    GIVEN: a feminine persona with an ACTIVE participacion in a MIXED discipline
    WHEN:  an administrator saves a masculine gender
    THEN:  the form is accepted — a mixed discipline accepts any gender
    """
    persona = escenario_admin_genero_sin_conflictos["personas"]["F"]

    form = PersonaAdminForm(
        data=_datos_persona(persona, genero=GeneroChoices.MASCULINO),
        instance=persona,
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_admin_no_bloquea_un_guardado_que_no_cambia_el_genero(
    escenario_auditoria_genero,
):
    """
    GIVEN: a persona with an incompatible ACTIVE participacion
    WHEN:  an administrator saves the SAME gender
    THEN:  the form is accepted — the guard only runs on a real change
    """
    persona = escenario_auditoria_genero["personas"]["F"]

    form = PersonaAdminForm(
        data=_datos_persona(persona),
        instance=persona,
    )

    assert form.is_valid() is True


# ── Phase 2: the Disciplina.modalidad guard ──────────────────────────────────


@pytest.mark.django_db
def test_admin_rechaza_cambiar_la_modalidad_con_participantes_activos_incompatibles(
    escenario_auditoria_genero,
):
    """
    GIVEN: a masculine discipline with an ACTIVE masculine participant
    WHEN:  an administrator saves a feminine modality
    THEN:  the form is rejected with a field error on `modalidad`
    AND:   the original modality is preserved in the database
    """
    disciplina = escenario_auditoria_genero["disciplinas"]["M"]

    form = DisciplinaAdminForm(
        data=_datos_disciplina(disciplina, modalidad=ModalidadChoices.FEMENINO),
        instance=disciplina,
    )

    assert form.is_valid() is False
    assert "modalidad" in form.errors
    assert len(_mensajes_de_error(form)) == 1

    disciplina.refresh_from_db()
    assert disciplina.modalidad == ModalidadChoices.MASCULINO


@pytest.mark.django_db
def test_admin_permite_cambiar_la_modalidad_a_mixta(
    escenario_auditoria_genero,
):
    """
    GIVEN: a masculine discipline with ACTIVE participants of both genders
    WHEN:  an administrator saves a mixed modality
    THEN:  the form is accepted — a mixed discipline accepts any gender
    """
    disciplina = escenario_auditoria_genero["disciplinas"]["M"]

    form = DisciplinaAdminForm(
        data=_datos_disciplina(disciplina, modalidad=ModalidadChoices.MIXTO),
        instance=disciplina,
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_admin_el_historial_retirado_no_bloquea_el_cambio_de_modalidad(
    escenario_admin_genero_sin_conflictos,
):
    """
    GIVEN: a masculine discipline whose only participacion is RETIRED
    WHEN:  an administrator saves a feminine modality
    THEN:  the form is accepted — the history is not an active conflict
    """
    disciplina = escenario_admin_genero_sin_conflictos["disciplinas"]["M"]

    form = DisciplinaAdminForm(
        data=_datos_disciplina(disciplina, modalidad=ModalidadChoices.FEMENINO),
        instance=disciplina,
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_admin_no_bloquea_un_guardado_de_disciplina_que_no_cambia_la_modalidad(
    escenario_auditoria_genero,
):
    """
    GIVEN: a discipline with incompatible ACTIVE participants
    WHEN:  an administrator saves the SAME modality
    THEN:  the form is accepted — the guard only runs on a real change
    """
    disciplina = escenario_auditoria_genero["disciplinas"]["M"]

    form = DisciplinaAdminForm(
        data=_datos_disciplina(disciplina),
        instance=disciplina,
    )

    assert form.is_valid() is True


# ── Phase 2: the Participacion admin safety net ──────────────────────────────


@pytest.mark.django_db
def test_admin_el_formulario_de_participacion_rechaza_una_participacion_activa_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a feminine persona and a masculine-only team
    WHEN:  an administrator saves an ACTIVE participacion
    THEN:  the form is rejected with a safe validation error
    AND:   the conflict is reported exactly once
    AND:   no participacion is created
    """
    escenario = escenario_genero_participacion

    form = ParticipacionAdminForm(
        data=_datos_participacion(
            escenario, "F", "M", EstadoParticipacionChoices.ACTIVA
        ),
    )

    assert form.is_valid() is False
    assert len(_mensajes_de_error(form)) == 1
    assert "no es compatible con el" in _mensajes_de_error(form)[0]
    assert not Participacion.objects.exists()


@pytest.mark.django_db
def test_admin_el_formulario_de_participacion_permite_una_participacion_activa_compatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a masculine persona and a masculine-only team
    WHEN:  an administrator saves an ACTIVE participacion
    THEN:  the form is accepted
    """
    escenario = escenario_genero_participacion

    form = ParticipacionAdminForm(
        data=_datos_participacion(
            escenario, "M", "M", EstadoParticipacionChoices.ACTIVA
        ),
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_admin_el_formulario_de_participacion_permite_el_historial_retirado_incompatible(
    escenario_genero_participacion,
):
    """
    GIVEN: a feminine persona and a masculine-only team
    WHEN:  an administrator saves a RETIRED participacion
    THEN:  the form is accepted — the history stays remediable
    """
    escenario = escenario_genero_participacion

    form = ParticipacionAdminForm(
        data=_datos_participacion(
            escenario, "F", "M", EstadoParticipacionChoices.RETIRADA
        ),
    )

    assert form.is_valid() is True


def test_admin_los_formularios_reutilizan_el_predicado_compartido():
    """
    GIVEN: the admin forms and the shared domain predicate
    WHEN:  the form modules are inspected
    THEN:  they IMPORT the predicate instead of keeping a private copy
    AND:   both call the very same function object
    """
    import inspect

    from modules.salesianos_fest import forms as forms_fest
    from modules.usuarios import forms as forms_usuarios

    assert (
        forms_fest.es_genero_compatible_con_modalidad
        is es_genero_compatible_con_modalidad
    )
    assert (
        forms_usuarios.es_genero_compatible_con_modalidad
        is es_genero_compatible_con_modalidad
    )
    assert "def es_genero_compatible_con_modalidad" not in inspect.getsource(forms_fest)
    assert "def es_genero_compatible_con_modalidad" not in inspect.getsource(forms_usuarios)


# ── Phase 2: the admin view wiring ───────────────────────────────────────────


@pytest.fixture
def admin_usuario(db):
    """Superuser with a persona (the admin view needs a logged in staff)."""
    User = get_user_model()
    persona = Persona.objects.create(
        nombres="Administrador",
        apellidos="Genero",
        tipo_documento="DNI",
        numero_documento="90009999",
        genero=GeneroChoices.MASCULINO,
    )
    return User.objects.create_superuser(
        username="admin_genero",
        password="testpass123",
        email="admin_genero@example.com",
        persona_fk=persona,
    )


@pytest.fixture
def admin_client(db, admin_usuario):
    """Django test client logged in as the admin (the admin is not an API)."""
    client = Client()
    client.force_login(admin_usuario)
    return client


@pytest.mark.django_db
def test_admin_el_panel_rechaza_el_cambio_de_genero_y_no_guarda(
    escenario_auditoria_genero,
    admin_client,
):
    """
    GIVEN: an administrator in the Django admin
    WHEN:  it saves an incompatible gender
    THEN:  the change form comes back with the field error
    AND:   the original gender is preserved in the database
    """
    persona = escenario_auditoria_genero["personas"]["F"]

    # The admin template renders the static assets; the manifest storage is
    # not built in the test environment, so the plain storage is used here.
    with override_settings(
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
    ):
        response = admin_client.post(
            reverse("admin:usuarios_persona_change", args=[persona.pk]),
            data=_datos_persona(persona, genero=GeneroChoices.MASCULINO),
        )

    assert response.status_code == 200
    assert "genero" in response.context["adminform"].form.errors

    persona.refresh_from_db()
    assert persona.genero == GeneroChoices.FEMENINO


# ── Phase 3: the advisory verdict of the participant selector ─────────────────
#
# The selector is the READ side of the same rule: it reports the candidate as
# NOT assignable BEFORE the responsable tries to submit, so the incompatible
# choice is disabled/identified with a UI-safe reason. The write path stays
# authoritative — the 409 `GENERO_NO_PERMITIDO` still rejects a bypass.


def _elegibles(inscripcion, equipo):
    """Read the candidate list of one team (the selector the modal consumes)."""
    return InscripcionSelector.get_elegibles_equipo(
        str(inscripcion.id),
        str(equipo.id),
    )


def _candidata(result, persona):
    """The candidate of `result` that belongs to `persona`."""
    return next(c for c in result.elegibles if c.persona_id == str(persona.id))


@pytest.mark.django_db
def test_elegibles_marca_incompatible_por_modalidad_como_no_asignable(
    escenario_genero_participacion,
):
    """
    GIVEN: a person WITH an active paid cup whose persisted gender is not
           accepted by the modality of the target discipline
    WHEN:  the eligible list of that team is read
    THEN:  the candidate is NOT assignable and the reason is the modality one
    AND:   the compatible candidate of the same team is NOT affected
    """
    escenario = escenario_genero_participacion

    result = _elegibles(escenario["inscripcion"], escenario["equipos"]["M"])

    incompatible = _candidata(result, escenario["personas"]["F"])
    assert incompatible.tiene_cupo_activo is True
    assert incompatible.estado_pool == "LISTO"
    assert incompatible.ya_en_disciplina is False
    assert incompatible.asignable is False
    assert incompatible.motivo_no_asignable == MOTIVO_GENERO_NO_COMPATIBLE

    compatible = _candidata(result, escenario["personas"]["M"])
    assert compatible.asignable is True
    assert compatible.motivo_no_asignable is None


@pytest.mark.django_db
def test_elegibles_marca_incompatible_en_la_disciplina_femenina(
    escenario_genero_participacion,
):
    """
    GIVEN: the symmetric case — a masculine person and a FEMININE team
    WHEN:  the eligible list of that team is read
    THEN:  the candidate is NOT assignable with the modality reason
    """
    escenario = escenario_genero_participacion

    result = _elegibles(escenario["inscripcion"], escenario["equipos"]["F"])

    incompatible = _candidata(result, escenario["personas"]["M"])
    assert incompatible.asignable is False
    assert incompatible.motivo_no_asignable == MOTIVO_GENERO_NO_COMPATIBLE

    compatible = _candidata(result, escenario["personas"]["F"])
    assert compatible.asignable is True
    assert compatible.motivo_no_asignable is None


@pytest.mark.django_db
def test_elegibles_una_disciplina_mixta_acepta_cualquier_genero(
    escenario_genero_participacion,
):
    """
    GIVEN: a MIXED (X) team
    WHEN:  the eligible list of that team is read
    THEN:  every candidate with a paid cup is assignable
    """
    escenario = escenario_genero_participacion

    result = _elegibles(escenario["inscripcion"], escenario["equipos"]["X"])

    for persona in escenario["personas"].values():
        candidata = _candidata(result, persona)
        assert candidata.asignable is True
        assert candidata.motivo_no_asignable is None


@pytest.mark.django_db
def test_elegibles_el_bloqueo_comercial_precede_a_la_modalidad(
    escenario_genero_participacion,
):
    """
    GIVEN: a candidate WITHOUT a paid cup whose gender is also incompatible
    WHEN:  the eligible list of that team is read
    THEN:  the candidate is blocked by the COMMERCIAL reason
    AND:   the modality reason does not hide the missing payment
    """
    escenario = escenario_genero_participacion
    inscripcion_persona = escenario["inscripciones_persona"]["F"]
    inscripcion_persona.asignaciones_cupo.all().update(estado="LIBERADA")

    result = _elegibles(escenario["inscripcion"], escenario["equipos"]["M"])

    candidata = _candidata(result, escenario["personas"]["F"])
    assert candidata.tiene_cupo_activo is False
    assert candidata.asignable is False
    assert candidata.motivo_no_asignable != MOTIVO_GENERO_NO_COMPATIBLE
    assert candidata.motivo_no_asignable == candidata.motivo_bloqueo


@pytest.mark.django_db
def test_elegibles_el_motivo_de_modalidad_no_expone_identificadores():
    """
    GIVEN: the UI-safe reason of the modality block
    WHEN:  it is read
    THEN:  it exposes no identifier, UUID, number or technical detail
    """
    motivo = MOTIVO_GENERO_NO_COMPATIBLE

    assert motivo
    assert not any(caracter.isdigit() for caracter in motivo)
    for tecnico in ("Traceback", "Exception", "SELECT", "uuid", "UUID", "None"):
        assert tecnico not in motivo


@pytest.mark.django_db
def test_elegibles_el_selector_reutiliza_el_predicado_compartido():
    """
    GIVEN: the advisory selector
    WHEN:  its source is inspected
    THEN:  it calls the shared predicate and keeps NO private matrix
    """
    import inspect

    from modules.salesianos_fest.domain.selectors import inscripcion_selector

    fuente = inspect.getsource(inscripcion_selector)

    assert "es_genero_compatible_con_modalidad" in fuente
    assert "def es_genero_compatible_con_modalidad" not in fuente
    assert "COMPATIBILIDADES_POR_GENERO" not in fuente


@pytest.mark.django_db(transaction=True)
def test_elegibles_la_api_expone_el_veredicto_de_modalidad(
    api_client,
    escenario_genero_participacion,
    usuario_responsable_genero,
):
    """
    GIVEN: the responsible of an inscription over HTTP
    WHEN:  it reads the eligible list of a team whose modality rejects a
           candidate
    THEN:  the response carries the same verdict and the same UI-safe reason
    AND:   the response contract does not change (same fields as before)
    """
    escenario = escenario_genero_participacion
    inscripcion = escenario["inscripcion"]
    equipo = escenario["equipos"]["M"]

    token = AccessToken.for_user(usuario_responsable_genero)
    response = api_client.get(
        f"/api/inscripciones/{inscripcion.id}/equipos/{equipo.id}/elegibles",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["equipo_id"] == str(equipo.id)
    assert data["disciplina"]["sigla"] == escenario["disciplinas"]["M"].sigla

    candidatas = {c["persona"]["id"]: c for c in data["elegibles"]}
    assert set(candidatas) == {
        str(escenario["personas"]["M"].id),
        str(escenario["personas"]["F"].id),
    }

    incompatible = candidatas[str(escenario["personas"]["F"].id)]
    assert incompatible["asignable"] is False
    assert incompatible["motivo_no_asignable"] == MOTIVO_GENERO_NO_COMPATIBLE
    assert incompatible["tiene_cupo_activo"] is True
    # The contract of the candidate does not change: the same fields as before.
    assert set(incompatible) == {
        "id",
        "persona",
        "estado",
        "created_at",
        "tiene_cupo_activo",
        "estado_pool",
        "motivo_bloqueo",
        "disciplinas_asignadas",
        "ya_en_disciplina",
        "asignable",
        "motivo_no_asignable",
    }

    compatible = candidatas[str(escenario["personas"]["M"].id)]
    assert compatible["asignable"] is True
    assert compatible["motivo_no_asignable"] is None
