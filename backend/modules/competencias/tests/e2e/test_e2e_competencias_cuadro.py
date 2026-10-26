"""
E2E — the administrative flow of a bracket of 3, 5, 6, 7 and 8 teams.

The suite walks the flow the administrator walks IN THE ADMINISTRATION and it
does it through the HTTP surface only (`ninja_extra.testing.TestAsyncClient`,
because the controllers are async —
`contract/django-app-architecture-contract.md` §2.1):

    create the competition → register the teams → create the rounds →
    create the encounters → configure the MANUAL byes → read the bracket →
    read the agenda of the day.

What it proves:

1. the bracket of 3, 5, 6, 7 and 8 teams is built and READ BACK as it was
   typed: the system NEVER invents a participant and NEVER chooses a bye,
2. the byes are exactly the MANUAL ones and a bye has one single
   participant, no schedule, no score and the participant as its winner,
3. the partial bracket stays legible: the later rounds keep their empty
   slots and their `BORRADOR` state,
4. the empty free text of the score (`marcador_detalle`) travels as the
   empty string — the shared `BaseSchema` must NOT normalize it to `None`
   (the focused assertion of the known normalization risk),
5. the agenda of ONE day lists only the encounters that have a schedule.
"""
import pytest

from modules.competencias.tests.factories import (
    FECHA_COMPETENCIA_ISO,
    HORA_FIN_ISO,
    HORA_INICIO_ISO,
    make_programacion_http_payload,
)

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"

EQUIPOS = (3, 5, 6, 7, 8)


@pytest.mark.parametrize("num_equipos", EQUIPOS)
@pytest.mark.django_db(transaction=True)
async def test_e2e_el_cuadro_manual_se_crea_y_se_lee_sin_inventar_nada(
    cliente_admin_competencias,
    constructor_cuadro_http,
    num_equipos,
):
    """
    GIVEN: an administrator with N teams
    WHEN: it types the bracket and reads it back
    THEN: the bracket is exactly the one it typed (nothing invented)
    """
    construido = await constructor_cuadro_http(num_equipos)
    competencia_id = construido["competencia_id"]
    plan = construido["plan"]

    respuesta = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/{competencia_id}/cuadro"
    )

    assert respuesta.status_code == 200
    cuadro = respuesta.json()["data"]

    # The competition and its teams are the ones of the administrator.
    assert cuadro["competencia_id"] == competencia_id
    assert cuadro["total_equipos"] == num_equipos

    # The columns are the rounds of the plan, in their manual order.
    columnas = sorted(cuadro["rondas"], key=lambda ronda: ronda["orden"])
    assert [columna["etiqueta"] for columna in columnas] == [
        ronda["etiqueta"] for ronda in plan["rondas"]
    ]

    for indice, ronda_plan in enumerate(plan["rondas"]):
        columna = columnas[indice]
        assert len(columna["encuentros"]) == len(ronda_plan["encuentros"])

        for posicion, encuentro_plan in enumerate(ronda_plan["encuentros"]):
            encuentro = columna["encuentros"][posicion]
            assert encuentro["orden"] == encuentro_plan["orden"]

            if indice == 0:
                # The FIRST round keeps the participants the administrator
                # typed (the entries of the bracket, not the raw teams).
                esperado_1 = (
                    construido["entradas"][encuentro_plan["participante_1"]]
                    if encuentro_plan["participante_1"] is not None
                    else None
                )
                esperado_2 = (
                    construido["entradas"][encuentro_plan["participante_2"]]
                    if encuentro_plan["participante_2"] is not None
                    else None
                )
                assert encuentro["participante_1_id"] == esperado_1
                assert encuentro["participante_2_id"] == esperado_2
            else:
                # The system NEVER invents a participant nor an advance.
                assert encuentro["participante_1_id"] is None
                assert encuentro["participante_2_id"] is None
                assert encuentro["estado"] == "BORRADOR"
                assert encuentro["es_bye"] is False
                assert encuentro["ganador_id"] is None

            # The empty free text of the score travels as the empty string:
            # the shared `BaseSchema` must not normalize it to `None`.
            assert encuentro["marcador_detalle"] == ""

    # The byes are EXACTLY the manual ones: one per odd bracket, none in an
    # even one.
    byes_leidos = [
        encuentro
        for columna in columnas
        for encuentro in columna["encuentros"]
        if encuentro["es_bye"]
    ]
    assert len(byes_leidos) == (1 if num_equipos % 2 else 0)

    for bye in byes_leidos:
        participantes = [
            participante
            for participante in (
                bye["participante_1_id"],
                bye["participante_2_id"],
            )
            if participante is not None
        ]
        # A bye has ONE participant, no schedule, no score and the
        # participant is its winner.
        assert len(participantes) == 1
        assert bye["inicio_programado"] is None
        assert bye["fin_programado"] is None
        assert bye["puntaje_1"] is None
        assert bye["puntaje_2"] is None
        assert bye["marcador_detalle"] == ""
        assert bye["estado"] == "FINALIZADO"
        assert bye["ganador_id"] == participantes[0]


@pytest.mark.django_db(transaction=True)
async def test_e2e_la_agenda_de_un_dia_muestra_los_encuentros_programados(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: a bracket with one scheduled encounter
    WHEN: the administrator reads the agenda of that day
    THEN: the agenda lists ONLY the encounter that has a schedule
    """
    construido = await constructor_cuadro_http(3)
    encuentro = construido["encuentros"][0]

    programado = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            encuentro["version"],
        ),
    )
    assert programado.status_code == 200

    agenda = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/agenda?fecha={FECHA_COMPETENCIA_ISO}"
    )

    assert agenda.status_code == 200
    cuerpo = agenda.json()["data"]
    assert cuerpo["fecha"] == FECHA_COMPETENCIA_ISO
    assert cuerpo["total"] == 1
    assert cuerpo["encuentros"][0]["id"] == encuentro["id"]
    assert cuerpo["encuentros"][0]["estado"] == "PROGRAMADO"


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_dia_sin_encuentros_es_una_agenda_vacia(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: a bracket without any schedule
    WHEN: the administrator reads the agenda of that day
    THEN: the agenda is EMPTY — never an error
    """
    await constructor_cuadro_http(3)

    agenda = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/agenda?fecha={FECHA_COMPETENCIA_ISO}"
    )

    assert agenda.status_code == 200
    cuerpo = agenda.json()["data"]
    assert cuerpo["total"] == 0
    assert cuerpo["encuentros"] == []
