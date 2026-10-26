"""
Integration tests — the operational overview (A1).

Covers the contract of `sdd/administracion-operativa-fest/admin-surface` §10:

1. authorization on every admin endpoint (401 / 403 / 200),
2. metric correctness on a hand-built fixture (EXACT numbers),
3. the event scope (rows of another edition are never counted),
4. the invariants: payment state ≠ registration state, persons ≠ participations,
   paid capacity from the PAGADA purchases,
5. a stable response wrapper (exact key sets),
6. no secret leakage,
7. no accidental mutation,
8. a CONSTANT query count (no N+1).

The HTTP client is `django.test.Client`: the controllers are async and this is
the pattern already established by the rest of the project
(`contract/django-app-architecture-contract.md` §2.1).
"""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.models import OrdenPago
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    AsignacionCupo,
    CompraInscripcion,
    ControlAcceso,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
)
from modules.usuarios.domain.models import Persona

URL_RESUMEN = "/api/administracion/resumen"

# Palabras que NUNCA deben viajar en una respuesta del área de administración.
CLAVES_PROHIBIDAS = (
    "password",
    "password_hash",
    "token",
    "codigo_qr",
    "metadata",
    "token_sesion",
    "transaction_id",
    "response_message",
    "is_superuser",
)


def _auth_header(user) -> dict:
    """Build the Authorization header of an authenticated user."""
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _snapshot() -> dict:
    """Snapshot the rows of every table the overview touches."""
    return {
        "eventos": Evento.objects.count(),
        "inscripciones": Inscripcion.objects.count(),
        "inscripciones_personas": InscripcionPersona.objects.count(),
        "equipos": Equipo.objects.count(),
        "participaciones": Participacion.objects.count(),
        "compras": Compra.objects.count(),
        "compras_inscripcion": CompraInscripcion.objects.count(),
        "asignaciones_cupo": AsignacionCupo.objects.count(),
        "acreditaciones": AcreditacionEvento.objects.count(),
        "controles_acceso": ControlAcceso.objects.count(),
        "ordenes_pago": OrdenPago.objects.count(),
        "personas": Persona.objects.count(),
        "cupos_activos": list(
            AsignacionCupo.objects.filter(estado="ACTIVA")
            .order_by("id")
            .values_list("id", "estado", "compra_id", "inscripcion_persona_id")
        ),
        "acreditaciones_estado": list(
            AcreditacionEvento.objects.order_by("id")
            .values_list("id", "estado", "acceso_fiesta", "autorizacion_fiesta")
        ),
        "compras_estado": list(
            Compra.objects.order_by("id").values_list("id", "estado", "total")
        ),
    }


# ── 401 — anonymous ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_anonimo_responde_401(api_client):
    """
    GIVEN: an anonymous caller
    WHEN:  GET /api/administracion/resumen
    THEN:  401 with the stable code AUTHENTICATION_REQUIRED.
    """
    response = api_client.get(URL_RESUMEN)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert body["data"] is None


# ── 403 — authenticated non-admin ─────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_no_admin_responde_403(api_client, usuario_no_admin):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/resumen
    THEN:  403 with the stable code ACTION_NOT_ALLOWED and no data.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_no_admin))

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert body["data"] is None


@pytest.mark.django_db
def test_resumen_no_admin_no_recibe_ninguna_metrica(
    api_client, usuario_no_admin, escenario_operativo
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/resumen
    THEN:  the body exposes none of the metrics of the event.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_no_admin))

    crudo = response.content.decode()
    assert "resumen" not in crudo
    assert "inscripciones" not in crudo
    assert "monto_pagado" not in crudo


# ── 200 — administrators ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_admin_staff_responde_200(api_client, usuario_admin_staff, evento):
    """
    GIVEN: an administrator (`is_staff`)
    WHEN:  GET /api/administracion/resumen
    THEN:  200 with the eight blocks of the overview.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert set(body["data"].keys()) == {
        "evento",
        "inscripciones",
        "pagos",
        "cupos",
        "equipos",
        "participantes",
        "acreditaciones",
        "accesos",
    }


@pytest.mark.django_db
def test_resumen_admin_superuser_responde_200(api_client, usuario_admin_superuser, evento):
    """
    GIVEN: an administrator (`is_superuser`)
    WHEN:  GET /api/administracion/resumen
    THEN:  200 — the break-glass tier is admin too.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_superuser))

    assert response.status_code == 200
    assert response.json()["data"]["evento"]["nombre"] == evento.nombre


# ── Event scope ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_usa_el_evento_activo_resuelto_en_el_servidor(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an active event and another (inactive) edition with its own rows
    WHEN:  GET /api/administracion/resumen
    THEN:  the event block reports the ACTIVE event and its id.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["evento"]["id"] == str(escenario_operativo["evento"].id)
    assert data["evento"]["nombre"] == escenario_operativo["evento"].nombre
    assert data["evento"]["esta_activo"] is True


@pytest.mark.django_db
def test_resumen_excluye_las_filas_de_otra_edicion(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an inscription, an accreditation and an access of ANOTHER edition
    WHEN:  GET /api/administracion/resumen
    THEN:  none of them enters the metrics of the active event.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["inscripciones"]["total"] == 2
    assert data["acreditaciones"]["total"] == 4
    assert data["accesos"]["permitidos"] == 1


@pytest.mark.django_db
def test_resumen_sin_evento_activo_responde_404(
    api_client, usuario_admin_staff
):
    """
    GIVEN: an administrator and NO active event in the database
    WHEN:  GET /api/administracion/resumen
    THEN:  404 with the stable code EVENTO_ACTIVO_NO_ENCONTRADO.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EVENTO_ACTIVO_NO_ENCONTRADO"
    assert body["data"] is None


# ── Exact metrics ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_inscripciones_tiene_las_metricas_exactas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: the hand-built scenario
    WHEN:  GET /api/administracion/resumen
    THEN:  the inscription block matches the expected numbers exactly.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["inscripciones"]
    assert data["inscripciones"]["total"] == esperado["total"]
    assert data["inscripciones"]["por_estado"] == esperado["por_estado"]
    assert (
        data["inscripciones"]["creadas_ultimos_7_dias"]
        == esperado["creadas_ultimos_7_dias"]
    )


@pytest.mark.django_db
def test_resumen_inscripciones_reporta_los_ocho_estados(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a scenario with only two states in use
    WHEN:  GET /api/administracion/resumen
    THEN:  the eight states are always present — a missing state means ZERO.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    por_estado = response.json()["data"]["inscripciones"]["por_estado"]
    assert set(por_estado.keys()) == {
        "BORRADOR",
        "RECIBIDA",
        "EN_REVISION",
        "OBSERVADA",
        "VALIDADA",
        "CONFIRMADA",
        "RECHAZADA",
        "CANCELADA",
    }
    assert por_estado["BORRADOR"] == 0


@pytest.mark.django_db
def test_resumen_pagos_tiene_las_metricas_exactas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: the hand-built scenario (5 purchases, 1 paid order not settled)
    WHEN:  GET /api/administracion/resumen
    THEN:  the payment block matches the expected numbers exactly.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["pagos"]
    assert data["pagos"] == esperado


@pytest.mark.django_db
def test_resumen_pagos_y_estado_de_inscripcion_son_independientes(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a registration whose state is RECIBIDA and whose purchase is PAGADA
    WHEN:  GET /api/administracion/resumen
    THEN:  the registration is NOT counted as paid and the purchase is NOT
           counted as a validated registration — the blocks are orthogonal.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["inscripciones"]["por_estado"]["RECIBIDA"] == 1
    assert data["inscripciones"]["por_estado"]["CONFIRMADA"] == 0
    assert data["pagos"]["compras_pagadas"] == 2


@pytest.mark.django_db
def test_resumen_cupos_usa_la_capacidad_pagada(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: purchases of 2 (paid) + 1 (pending) + 9 (cancelled) + 1 (paid) + 1 (pending)
    WHEN:  GET /api/administracion/resumen
    THEN:  `pagado` counts ONLY the PAGADA purchases and `disponible_pagado` is
           `pagado - asignado_activo`.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["cupos"]
    assert data["cupos"] == esperado
    assert data["cupos"]["pagado"] == 3
    assert data["cupos"]["asignado_activo"] == 2
    assert data["cupos"]["disponible_pagado"] == 1


@pytest.mark.django_db
def test_resumen_cupos_detecta_la_capacidad_exhaustada(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an inscription whose paid capacity is fully assigned
    WHEN:  GET /api/administracion/resumen
    THEN:  it is counted as an inscription with exhausted capacity.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["cupos"]["inscripciones_con_capacidad_exhaustada"] == 1


@pytest.mark.django_db
def test_resumen_equipos_tiene_las_metricas_exactas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: 3 active teams (2 complete, 1 incomplete) and 1 cancelled team
    WHEN:  GET /api/administracion/resumen
    THEN:  the team block matches the expected numbers exactly.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["equipos"]
    assert data["equipos"]["total"] == esperado["total"]
    assert data["equipos"]["completos"] == esperado["completos"]
    assert data["equipos"]["incompletos"] == esperado["incompletos"]

    por_disciplina = {
        item["sigla"]: item for item in data["equipos"]["por_disciplina"]
    }
    assert len(por_disciplina) == 2
    assert por_disciplina["F7"]["total"] == 2
    assert por_disciplina["F7"]["disciplina_id"] == str(
        escenario_operativo["disciplina_futbol"].id
    )
    assert por_disciplina["VM"]["total"] == 1


@pytest.mark.django_db
def test_resumen_participantes_distingue_personas_de_participaciones(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: 5 active people, 4 active participations, 2 in the pool, 3 without cup
    WHEN:  GET /api/administracion/resumen
    THEN:  the block matches the expected numbers exactly.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["participantes"]
    assert data["participantes"] == esperado


@pytest.mark.django_db
def test_resumen_personas_y_participaciones_no_se_confunden(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: one person playing in TWO disciplines
    WHEN:  GET /api/administracion/resumen
    THEN:  `personas_distintas` and `participaciones_activas` are DIFFERENT
           numbers — one paid cup authorises every contracted discipline.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    participantes = response.json()["data"]["participantes"]
    assert participantes["personas_distintas"] != participantes["participaciones_activas"]


@pytest.mark.django_db
def test_resumen_acreditaciones_tiene_las_metricas_exactas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: 4 accreditations (2 with effective access, 1 blocked by an admin)
    WHEN:  GET /api/administracion/resumen
    THEN:  the accreditation block matches the expected numbers exactly.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    esperado = escenario_operativo["esperado"]["acreditaciones"]
    assert data["acreditaciones"] == esperado


@pytest.mark.django_db
def test_resumen_acreditacion_bloqueada_no_cuenta_como_acceso(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an accreditation with acceso_fiesta=True but REVOCADA and bloqueada
    WHEN:  GET /api/administracion/resumen
    THEN:  it does NOT count as an effective fiesta access.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["acreditaciones"]["con_acceso_fiesta"] == 2
    assert data["acreditaciones"]["bloqueadas_por_admin"] == 1


@pytest.mark.django_db
def test_resumen_accesos_tiene_las_metricas_exactas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: 1 permitted access and 2 denied accesses of the active event
    WHEN:  GET /api/administracion/resumen
    THEN:  the access block matches the expected numbers and reports the last
           access instant.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    accesos = response.json()["data"]["accesos"]
    esperado = escenario_operativo["esperado"]["accesos"]
    assert accesos["permitidos"] == esperado["permitidos"]
    assert accesos["denegados"] == esperado["denegados"]
    assert accesos["ultimo_acceso"] is not None


# ── Stable response wrapper ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_respeta_el_envoltorio_estable(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/resumen
    THEN:  the envelope and every block expose EXACTLY the documented keys.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    body = response.json()
    assert set(body.keys()) == {"success", "data", "error", "message"}

    data = body["data"]
    assert set(data["evento"].keys()) == {
        "id",
        "nombre",
        "fecha_inicio",
        "fecha_fin",
        "esta_activo",
        "fecha_limite_modificacion",
        "puede_modificar",
    }
    assert set(data["inscripciones"].keys()) == {
        "total",
        "por_estado",
        "creadas_ultimos_7_dias",
    }
    assert set(data["pagos"].keys()) == {
        "compras_total",
        "compras_pagadas",
        "compras_pendientes",
        "compras_canceladas",
        "monto_pagado",
        "monto_pendiente",
        "ordenes_vencidas",
        "compras_pagadas_sin_liquidar",
    }
    assert set(data["cupos"].keys()) == {
        "contratado",
        "pagado",
        "asignado_activo",
        "disponible_pagado",
        "inscripciones_con_capacidad_exhaustada",
    }
    assert set(data["equipos"].keys()) == {
        "total",
        "completos",
        "incompletos",
        "por_disciplina",
    }
    assert set(data["participantes"].keys()) == {
        "personas_distintas",
        "participaciones_activas",
        "en_pool",
        "sin_cupo_activo",
    }
    assert set(data["acreditaciones"].keys()) == {
        "total",
        "por_estado",
        "con_acceso_fiesta",
        "bloqueadas_por_admin",
    }
    assert set(data["accesos"].keys()) == {"permitidos", "denegados", "ultimo_acceso"}


# ── Data-leak discipline ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_no_expone_credenciales_ni_metadatos(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/resumen
    THEN:  the body contains none of the forbidden keys — no QR, no token, no
           payment metadata.
    """
    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))

    crudo = response.content.decode().lower()
    for clave in CLAVES_PROHIBIDAS:
        assert clave not in crudo, f"La respuesta filtró la clave '{clave}'."


# ── No accidental mutation ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_no_muta_ninguna_tabla(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator and a populated database
    WHEN:  GET /api/administracion/resumen
    THEN:  no row of the touched tables changed.
    """
    antes = _snapshot()

    response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))
    assert response.status_code == 200

    assert _snapshot() == antes


# ── Constant query count (no N+1) ─────────────────────────────────────────────


@pytest.mark.django_db
def test_resumen_mantiene_un_numero_de_consultas_constante(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: the same event with more rows
    WHEN:  GET /api/administracion/resumen twice (before and after adding rows)
    THEN:  the number of queries is the SAME — the aggregates never scale with
           the number of rows.
    """
    with CaptureQueriesContext(connection) as contexto_inicial:
        response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))
    assert response.status_code == 200
    consultas_iniciales = len(contexto_inicial)

    # More rows of the same event: more inscriptions, people and teams.
    escenario = escenario_operativo
    for indice in range(3):
        persona = Persona.objects.create(
            nombres=f"Extra{indice}",
            apellidos="Participante",
            tipo_documento="DNI",
            numero_documento=f"9990000{indice}",
            genero="M",
        )
        responsable = Persona.objects.create(
            nombres=f"Responsable{indice}",
            apellidos="Adicional",
            tipo_documento="DNI",
            numero_documento=f"8880000{indice}",
            genero="M",
        )
        inscripcion = Inscripcion.objects.create(
            evento=escenario["evento"],
            responsable=responsable,
            paquete=escenario["paquete"],
            promocion=escenario["promocion"],
            estado="RECIBIDA",
        )
        InscripcionPersona.objects.create(
            inscripcion=inscripcion, persona=persona, estado="A"
        )

    with CaptureQueriesContext(connection) as contexto_final:
        response = api_client.get(URL_RESUMEN, **_auth_header(usuario_admin_staff))
    assert response.status_code == 200
    consultas_finales = len(contexto_final)

    assert consultas_finales == consultas_iniciales
