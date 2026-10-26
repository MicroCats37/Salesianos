"""
E2E — the authorization of the two surfaces of the bracket.

The module has TWO surfaces and they do NOT share the same rule
(`contract/api-wrapper-presenter-contract.md` §9):

- the ADMINISTRATIVE surface is gated by `RequireAdmin` (is_staff OR
  is_superuser): an anonymous caller gets 401 and an authenticated non
  administrator gets 403,
- the PUBLIC surface is READ-ONLY and limited to the editions the reader is
  authorized for: a competition outside of the scope is answered with 404
  `COMPETENCIA_NOT_FOUND` — the surface never confirms the existence of a
  resource the reader cannot see.
"""
import pytest

from modules.competencias.tests.factories import (
    make_competencia_create_http_payload,
    make_encuentro_create_http_payload,
)

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"
URL_PUBLICA = "/competencias"


# ── La superficie administrativa exige un administrador ──────────────────────


@pytest.mark.django_db(transaction=True)
async def test_e2e_una_escritura_sin_token_es_401(
    cliente_api_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an anonymous caller
    WHEN: it tries to create a competition
    THEN: 401 `AUTHENTICATION_REQUIRED` and NOTHING is written
    """
    respuesta = await cliente_api_competencias.post(
        URL_ADMIN,
        json=make_competencia_create_http_payload(
            evento_competencia.id,
            disciplina_competencia.id,
            categoria_competencia.id,
            nombre="Eliminatoria anonima",
        ),
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db(transaction=True)
async def test_e2e_una_escritura_de_un_usuario_normal_es_403(
    cliente_no_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN: it tries to create a competition
    THEN: 403 `ACTION_NOT_ALLOWED` and NOTHING is written
    """
    respuesta = await cliente_no_admin_competencias.post(
        URL_ADMIN,
        json=make_competencia_create_http_payload(
            evento_competencia.id,
            disciplina_competencia.id,
            categoria_competencia.id,
            nombre="Eliminatoria de un usuario normal",
        ),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db(transaction=True)
async def test_e2e_una_lectura_administrativa_sin_token_es_401(
    cliente_api_competencias,
    competencia,
):
    """
    GIVEN: an anonymous caller
    WHEN: it tries to read the administrative bracket
    THEN: 401 `AUTHENTICATION_REQUIRED`
    """
    respuesta = await cliente_api_competencias.get(f"{URL_ADMIN}/{competencia.id}")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_comando_de_encuentro_de_un_usuario_normal_es_403(
    cliente_no_admin_competencias,
    encuentro,
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN: it tries to move the participants of an encounter
    THEN: 403 `ACTION_NOT_ALLOWED`
    """
    respuesta = await cliente_no_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro.id}/participantes",
        json={
            "participante_1_id": None,
            "participante_2_id": None,
            "motivo": "Intento de escritura sin permisos",
            "expected_version": encuentro.version,
        },
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


# ── La superficie pública solo lee y solo del alcance autorizado ────────────


@pytest.mark.django_db(transaction=True)
async def test_e2e_la_superficie_publica_solo_lee_el_alcance_autorizado(
    cliente_api_competencias,
    competencia,
    competencia_fuera_de_alcance,
):
    """
    GIVEN: a competition of an ACTIVE edition and one of a CLOSED edition
    WHEN: the public reader asks for both
    THEN: the first one is served and the second one is 404 (never 403)
    """
    visible = await cliente_api_competencias.get(f"{URL_PUBLICA}/{competencia.id}")
    assert visible.status_code == 200
    assert visible.json()["data"]["id"] == str(competencia.id)

    fuera = await cliente_api_competencias.get(
        f"{URL_PUBLICA}/{competencia_fuera_de_alcance.id}"
    )
    assert fuera.status_code == 404
    assert fuera.json()["error"]["code"] == "COMPETENCIA_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
async def test_e2e_el_cuadro_fuera_del_alcance_tampoco_se_sirve(
    cliente_api_competencias,
    competencia_fuera_de_alcance,
):
    """
    GIVEN: a competition of a CLOSED edition
    WHEN: the public reader asks for its bracket
    THEN: 404 `COMPETENCIA_NOT_FOUND` — the surface leaks nothing
    """
    respuesta = await cliente_api_competencias.get(
        f"{URL_PUBLICA}/{competencia_fuera_de_alcance.id}/cuadro"
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "COMPETENCIA_NOT_FOUND"


@pytest.mark.django_db(transaction=True)
async def test_e2e_la_lista_publica_solo_trae_el_alcance_autorizado(
    cliente_api_competencias,
    competencia,
    competencia_fuera_de_alcance,
):
    """
    GIVEN: a competition of an ACTIVE edition and one of a CLOSED edition
    WHEN: the public reader asks for the list
    THEN: only the authorized one is listed
    """
    respuesta = await cliente_api_competencias.get(URL_PUBLICA)

    assert respuesta.status_code == 200
    assert [fila["id"] for fila in respuesta.json()["data"]] == [str(competencia.id)]


@pytest.mark.django_db(transaction=True)
async def test_e2e_la_superficie_publica_no_acepta_escrituras(
    cliente_api_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """
    GIVEN: an anonymous caller
    WHEN: it tries to write through the PUBLIC surface
    THEN: the route does not exist — the public surface is READ-ONLY
    """
    respuesta = await cliente_api_competencias.post(
        URL_PUBLICA,
        json=make_competencia_create_http_payload(
            evento_competencia.id,
            disciplina_competencia.id,
            categoria_competencia.id,
            nombre="Eliminatoria publica",
        ),
    )

    assert respuesta.status_code in (404, 405)


@pytest.mark.django_db(transaction=True)
async def test_e2e_la_superficie_publica_no_expone_los_encuentros_de_admin(
    cliente_api_competencias,
    competencia,
    ronda,
):
    """
    GIVEN: a competition with a round
    WHEN: the public reader asks for the encounters of the administrative
    surface
    THEN: the route does NOT exist — the commands are NOT public
    """
    with pytest.raises(Exception, match="Cannot resolve"):
        await cliente_api_competencias.post(
            f"{URL_PUBLICA}/{competencia.id}/encuentros",
            json=make_encuentro_create_http_payload(ronda.id, 99),
        )
