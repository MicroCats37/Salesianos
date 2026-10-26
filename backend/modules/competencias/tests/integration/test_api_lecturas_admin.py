"""
Integration tests — the ADMINISTRATIVE read surface of the bracket (Phase 3).

The HTTP client is `ninja_extra.testing.TestAsyncClient`: the controllers are
async (`contract/django-app-architecture-contract.md` §2.1).

What this file proves:

1. the authorization of the administrative surface: 401 without a token,
   403 for an authenticated non administrator and 200 for an administrator,
2. the statuses and the standard wrapper of every read,
3. the filters of the list,
4. the agenda of ONE day (populated and empty),
5. the detail with its teams and its rounds.
"""
import pytest

URL_ADMIN = "/administracion/competencias"

INICIO_DIA = "2026-11-16T10:00:00-05:00"
FIN_DIA = "2026-11-16T11:00:00-05:00"
MOTIVO_HORARIO = "Programacion del encuentro del cuadro de pruebas"


def _cuerpo(response):
    """Return the body of the standard wrapper."""
    return response.json()


# ── Autorización ────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_sin_token_es_401(cliente_api_competencias, competencia):
    """
    GIVEN: an anonymous caller
    WHEN: it asks for the administrative list
    THEN: 401 `AUTHENTICATION_REQUIRED` — the JWT answers before the permission
    """
    response = await cliente_api_competencias.get(URL_ADMIN)

    assert response.status_code == 401
    cuerpo = _cuerpo(response)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_de_un_usuario_normal_es_403(
    cliente_no_admin_competencias,
    competencia,
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN: it asks for the administrative list
    THEN: 403 `ACTION_NOT_ALLOWED`
    """
    response = await cliente_no_admin_competencias.get(URL_ADMIN)

    assert response.status_code == 403
    cuerpo = _cuerpo(response)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_de_un_administrador_es_200(
    cliente_admin_competencias,
    competencia,
):
    """
    GIVEN: an administrator
    WHEN: it asks for the administrative list
    THEN: 200 with the standard wrapper
    """
    response = await cliente_admin_competencias.get(URL_ADMIN)

    assert response.status_code == 200
    assert _cuerpo(response)["success"] is True


# ── Lecturas ────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_lista_con_filtros(
    cliente_admin_competencias,
    competencia,
    disciplina_competencia_2,
):
    """
    GIVEN: a competition of one discipline
    WHEN: the administrator filters by another discipline
    THEN: the list is empty, and without filters the row is returned
    """
    filtrada = await cliente_admin_competencias.get(
        f"{URL_ADMIN}?disciplina_id={disciplina_competencia_2.id}"
    )
    completa = await cliente_admin_competencias.get(URL_ADMIN)

    assert filtrada.status_code == 200
    assert _cuerpo(filtrada)["data"] == []
    assert [f["id"] for f in _cuerpo(completa)["data"]] == [str(competencia.id)]


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_detalle_con_equipos_y_rondas(
    cliente_admin_competencias,
    competencia,
    competencia_equipo,
    ronda,
):
    """
    GIVEN: a competition with a team and a round
    WHEN: the administrator asks for its detail
    THEN: 200 with the teams, the rounds and the counters
    """
    response = await cliente_admin_competencias.get(f"{URL_ADMIN}/{competencia.id}")

    assert response.status_code == 200
    detalle = _cuerpo(response)["data"]
    assert detalle["id"] == str(competencia.id)
    assert len(detalle["equipos"]) == 1
    assert detalle["equipos"][0]["id"] == str(competencia_equipo.id)
    assert detalle["equipos"][0]["equipo_nombre"] == "Equipo Alfa"
    assert len(detalle["rondas"]) == 1
    assert detalle["rondas"][0]["etiqueta"] == "Cuartos de final"
    assert detalle["rondas"][0]["total_encuentros"] == 0


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_de_una_competencia_desconocida_es_404(
    cliente_admin_competencias,
):
    """
    GIVEN: an id that does not exist
    WHEN: the administrator asks for its detail
    THEN: 404 `COMPETENCIA_NOT_FOUND`
    """
    response = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert _cuerpo(response)["error"]["code"] == "COMPETENCIA_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_agenda_de_un_dia_sin_encuentros(
    cliente_admin_competencias,
    competencia,
):
    """
    GIVEN: a day without scheduled encounters
    WHEN: the administrator asks for the agenda of that day
    THEN: 200 with an EMPTY agenda — never an error
    """
    response = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/agenda?fecha=2026-11-16"
    )

    assert response.status_code == 200
    agenda = _cuerpo(response)["data"]
    assert agenda["fecha"] == "2026-11-16"
    assert agenda["total"] == 0
    assert agenda["encuentros"] == []


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_agenda_de_un_dia_con_encuentros(
    cliente_admin_competencias,
    competencia,
    encuentro,
):
    """
    GIVEN: an encounter scheduled that day
    WHEN: the administrator asks for the agenda of that day
    THEN: 200 with the encounter in the agenda
    """
    programacion = await cliente_admin_competencias.patch(
        f"{URL_ADMIN}/encuentros/{encuentro.id}/programacion",
        json={
            "inicio_programado": INICIO_DIA,
            "fin_programado": FIN_DIA,
            "motivo": MOTIVO_HORARIO,
            "expected_version": encuentro.version,
        },
    )
    assert programacion.status_code == 200

    response = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/agenda?fecha=2026-11-16"
    )

    assert response.status_code == 200
    agenda = _cuerpo(response)["data"]
    assert agenda["total"] == 1
    assert agenda["encuentros"][0]["id"] == str(encuentro.id)
    assert agenda["encuentros"][0]["estado"] == "PROGRAMADO"
    assert agenda["encuentros"][0]["ronda_etiqueta"] == "Cuartos de final"


@pytest.mark.django_db(transaction=True)
async def test_lectura_admin_cuadro_de_la_competencia(
    cliente_admin_competencias,
    competencia,
    ronda,
    encuentro,
):
    """
    GIVEN: a bracket with one round and one encounter
    WHEN: the administrator asks for the bracket
    THEN: 200 with the rounds and their encounters
    """
    response = await cliente_admin_competencias.get(f"{URL_ADMIN}/{competencia.id}/cuadro")

    assert response.status_code == 200
    cuadro = _cuerpo(response)["data"]
    assert len(cuadro["rondas"]) == 1
    assert len(cuadro["rondas"][0]["encuentros"]) == 1
