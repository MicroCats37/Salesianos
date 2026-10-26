"""Integration tests for teams, participants and roster rows (A7-A9)."""

import pytest

from modules.administracion.tests.factories import make_auth_header, make_list_query


URL_EQUIPOS = "/api/administracion/equipos"
URL_PARTICIPANTES = "/api/administracion/participantes"
URL_PARTICIPACIONES = "/api/administracion/participaciones"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [URL_EQUIPOS, URL_PARTICIPANTES, URL_PARTICIPACIONES],
)
def test_listas_anonimo_responden_401(api_client, url):
    response = api_client.get(url)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [URL_EQUIPOS, URL_PARTICIPANTES, URL_PARTICIPACIONES],
)
def test_listas_no_admin_responden_403(api_client, usuario_no_admin, url):
    response = api_client.get(url, **make_auth_header(usuario_no_admin))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_equipos_exponen_roster_derivado_exacto(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(URL_EQUIPOS, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 4
    equipos = {item["nombre"]: item for item in data["items"]}

    assert equipos["Los Tigres"]["jugadores_registrados"] == 2
    assert equipos["Los Tigres"]["estado_roster"] == "COMPLETO"
    assert equipos["Las Panteras"]["jugadores_registrados"] == 1
    assert equipos["Las Panteras"]["estado_roster"] == "COMPLETO"
    assert equipos["Los Leones"]["jugadores_registrados"] == 1
    assert equipos["Los Leones"]["faltantes"] == 1
    assert equipos["Los Leones"]["estado_roster"] == "INCOMPLETO"


@pytest.mark.django_db
def test_filtros_de_equipo_se_aplican_antes_de_paginar(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)

    activos = api_client.get(
        URL_EQUIPOS,
        **headers,
        data=make_list_query(estado="EQUIPO_ACTIVO", page_size=1),
    ).json()["data"]
    assert activos["total"] == 3
    assert len(activos["items"]) == 1

    completos = api_client.get(
        URL_EQUIPOS, **headers, data=make_list_query(roster="COMPLETO")
    ).json()["data"]
    assert completos["total"] == 2

    por_disciplina = api_client.get(
        URL_EQUIPOS,
        **headers,
        data=make_list_query(
            disciplina_id=str(escenario_operativo["disciplina_voley"].id)
        ),
    ).json()["data"]
    assert por_disciplina["total"] == 1
    assert por_disciplina["items"][0]["nombre"] == "Las Panteras"


@pytest.mark.django_db
def test_participantes_exponen_pool_y_cupo_derivados(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(
        URL_PARTICIPANTES, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 6
    personas = {item["persona_documento"]: item for item in data["items"]}

    assert personas["33333333"]["estado_pool"] == "LISTO"
    assert personas["33333333"]["tiene_cupo_activo"] is True
    assert personas["44444444"]["estado_pool"] == "CUPO_POR_ASIGNAR"
    assert personas["44444444"]["disciplinas"] == ["F7", "VM"]
    assert personas["55555555"]["estado_pool"] == "SIN_CAPACIDAD"
    assert personas["77777777"]["estado"] == "R"


@pytest.mark.django_db
def test_filtros_de_participantes_distinguen_pool_y_disciplina(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)

    con_cupo = api_client.get(
        URL_PARTICIPANTES, **headers, data=make_list_query(con_cupo="true")
    ).json()["data"]
    assert con_cupo["total"] == 2
    assert all(item["tiene_cupo_activo"] for item in con_cupo["items"])

    por_asignar = api_client.get(
        URL_PARTICIPANTES,
        **headers,
        data=make_list_query(estado_pool="CUPO_POR_ASIGNAR"),
    ).json()["data"]
    assert por_asignar["total"] == 1
    assert por_asignar["items"][0]["persona_documento"] == "44444444"

    voley = api_client.get(
        URL_PARTICIPANTES,
        **headers,
        data=make_list_query(
            disciplina_id=str(escenario_operativo["disciplina_voley"].id)
        ),
    ).json()["data"]
    assert voley["total"] == 1
    assert voley["items"][0]["disciplinas"] == ["F7", "VM"]


@pytest.mark.django_db
def test_participaciones_son_filas_de_roster_independientes(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(
        URL_PARTICIPACIONES, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 5

    lucia = [
        item for item in data["items"] if item["persona_documento"] == "44444444"
    ]
    assert len(lucia) == 2
    assert {item["disciplina_sigla"] for item in lucia} == {"F7", "VM"}

    activas = api_client.get(
        URL_PARTICIPACIONES,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(estado="A"),
    ).json()["data"]
    assert activas["total"] == 4


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "parametro", "valor"),
    [
        (URL_EQUIPOS, "roster", "CASI_COMPLETO"),
        (URL_EQUIPOS, "estado", "NO_EXISTE"),
        (URL_PARTICIPANTES, "con_cupo", "quizas"),
        (URL_PARTICIPANTES, "estado_pool", "NO_EXISTE"),
        (URL_PARTICIPACIONES, "rol", "NO_EXISTE"),
        (URL_PARTICIPACIONES, "estado", "NO_EXISTE"),
        (URL_PARTICIPACIONES, "ordering", "persona; DROP TABLE roster"),
    ],
)
def test_filtros_invalidos_responden_422(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    url,
    parametro,
    valor,
):
    response = api_client.get(
        url,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(**{parametro: valor}),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_endpoints_de_equipos_y_participantes_no_mutan_datos(
    api_client, usuario_admin_staff, escenario_operativo
):
    from modules.salesianos_fest.domain.models import (
        Equipo,
        InscripcionPersona,
        Participacion,
    )

    antes = (
        Equipo.objects.count(),
        InscripcionPersona.objects.count(),
        Participacion.objects.count(),
    )
    headers = make_auth_header(usuario_admin_staff)

    for url in (URL_EQUIPOS, URL_PARTICIPANTES, URL_PARTICIPACIONES):
        api_client.get(url, **headers)

    assert antes == (
        Equipo.objects.count(),
        InscripcionPersona.objects.count(),
        Participacion.objects.count(),
    )
