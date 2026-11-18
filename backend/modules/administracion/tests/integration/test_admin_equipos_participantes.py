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
    assert equipos["Los Leones"]["estado_roster"] == "INCOMPLETO"


@pytest.mark.django_db
def test_equipos_publican_minimo_maximo_y_estado_de_capacidad(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: teams of the active event WHEN: the list is read
    THEN: the minimum and the maximum are published as TWO facts, the
    capacity verdict is published by the server and the misleading
    `faltantes` is gone.
    """
    response = api_client.get(URL_EQUIPOS, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    equipos = {item["nombre"]: item for item in response.json()["data"]["items"]}

    # The minimum is the minimum to COMPETE; the maximum is the hard cap.
    assert equipos["Los Tigres"]["minimo_deportivo"] == 2
    assert equipos["Los Tigres"]["maximo_deportivo"] == 11
    assert equipos["Las Panteras"]["minimo_deportivo"] == 1
    assert equipos["Las Panteras"]["maximo_deportivo"] == 12

    # The capacity is a SERVER verdict, not a comparison made by the client.
    assert equipos["Los Tigres"]["estado_capacidad"] == "CON_CUPOS"
    assert equipos["Las Panteras"]["estado_capacidad"] == "CON_CUPOS"
    assert equipos["Los Leones"]["estado_capacidad"] == "CON_CUPOS"

    # The state of the OWNING registration is visible on the row.
    assert equipos["Los Tigres"]["inscripcion_estado"] == "RECIBIDA"
    assert equipos["Los Leones"]["inscripcion_estado"] == "VALIDADA"

    # `faltantes` was never rendered and it duplicated the minimum.
    assert "faltantes" not in equipos["Los Tigres"]


@pytest.mark.django_db
def test_equipo_al_tope_se_publica_como_al_limite(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: a team that reached the cap of its discipline
    WHEN: the list is read THEN: the server publishes `AL_LIMITE`.
    """
    from modules.salesianos_fest.domain.constants import (
        EstadoEquipoChoices,
        EstadoParticipacionChoices,
        ModalidadChoices,
        RolParticipanteChoices,
    )
    from modules.salesianos_fest.domain.models import (
        Disciplina,
        Equipo,
        InscripcionPersona,
        Participacion,
    )

    disciplina_corta = Disciplina.objects.create(
        nombre="Fútbol 1",
        sigla="F1",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=1,
        max_jugadores=1,
        esta_activa=True,
    )
    equipo_lleno = Equipo.objects.create(
        inscripcion=escenario_operativo["inscripcion_1"],
        disciplina=disciplina_corta,
        nombre="Equipo Lleno",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    persona_registrada = InscripcionPersona.objects.filter(
        inscripcion_id=escenario_operativo["inscripcion_1"].id
    ).first()
    Participacion.objects.create(
        inscripcion_persona=persona_registrada,
        equipo=equipo_lleno,
        evento=escenario_operativo["evento"],
        disciplina=disciplina_corta,
        persona=persona_registrada.persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    response = api_client.get(URL_EQUIPOS, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    equipos = {item["nombre"]: item for item in response.json()["data"]["items"]}

    assert equipos["Equipo Lleno"]["jugadores_registrados"] == 1
    assert equipos["Equipo Lleno"]["maximo_deportivo"] == 1
    assert equipos["Equipo Lleno"]["estado_capacidad"] == "AL_LIMITE"
    # The degenerate case `min == max` is decided by the same rule.
    assert equipos["Equipo Lleno"]["estado_roster"] == "COMPLETO"


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
    assert personas["44444444"]["estado_pool"] == "CUPO_POR_ASIGNAR"
    assert personas["44444444"]["disciplinas"] == ["F7", "VM"]
    assert personas["55555555"]["estado_pool"] == "SIN_CAPACIDAD"
    assert personas["77777777"]["estado"] == "R"


@pytest.mark.django_db
def test_participantes_no_publiquen_el_cupo_activo_redundante(
    api_client, usuario_admin_staff, escenario_operativo
):
    """GIVEN: the participants of the pool
    WHEN: the list is read
    THEN: the pool verdict is the ONLY state published, the reason of the
    block travels with it and the redundant `tiene_cupo_activo` is gone.
    """
    response = api_client.get(
        URL_PARTICIPANTES, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    personas = {
        item["persona_documento"]: item for item in response.json()["data"]["items"]
    }

    assert "tiene_cupo_activo" not in personas["33333333"]

    # The reason of the block travels WITH the verdict, not in a sibling column.
    assert personas["44444444"]["motivo_bloqueo"]
    assert personas["33333333"]["motivo_bloqueo"] is None


@pytest.mark.django_db
def test_filtros_de_participantes_distinguen_pool_y_disciplina(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)

    con_cupo = api_client.get(
        URL_PARTICIPANTES, **headers, data=make_list_query(con_cupo="true")
    ).json()["data"]
    assert con_cupo["total"] == 2
    # The filter by cup survives; the ROW publishes only the pool verdict.
    assert all(item["estado_pool"] == "LISTO" for item in con_cupo["items"])

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
