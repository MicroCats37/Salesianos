"""
E2E — concurrency, optimistic lock and idempotency through the HTTP surface.

The guarantees of the spec are locked down here with the SAME client the
browser uses (`ninja_extra.testing.TestAsyncClient`, because the controllers
are async — `contract/django-app-architecture-contract.md` §2.1):

1. two administrators that edit the SAME version: only the FIRST one applies
   and the second one fails with 409 `RESOURCE_CHANGED` — WITHOUT partial
   effects,
2. a repeated command with the same intention is idempotent: it answers 200
   and writes NOTHING (not even a version bump),
3. a team cannot play two encounters at the same time: the second schedule
   fails with 409 `EQUIPO_SOLAPADO`.
"""
from datetime import datetime, timezone

import pytest

from modules.competencias.tests.factories import (
    HORA_FIN_ENCADENADO_ISO,
    HORA_FIN_ISO,
    HORA_FIN_SOLAPADO_ISO,
    HORA_FIN_TARDE_ISO,
    HORA_INICIO_ENCADENADO_ISO,
    HORA_INICIO_ISO,
    HORA_INICIO_SOLAPADO_ISO,
    HORA_INICIO_TARDE_ISO,
    make_encuentro_create_http_payload,
    make_programacion_http_payload,
)

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"


def _a_utc(iso: str) -> datetime:
    """Return the instant of an ISO timestamp as an aware UTC datetime."""
    valor = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


@pytest.mark.django_db(transaction=True)
async def test_e2e_dos_ediciones_con_la_misma_version_solo_aplica_una(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: two administrators editing the same version of an encounter
    WHEN: both confirm a DIFFERENT schedule
    THEN: only the first one applies and the second one gets 409
    `RESOURCE_CHANGED` with NO partial effect
    """
    construido = await constructor_cuadro_http(3)
    competencia_id = construido["competencia_id"]
    encuentro = construido["encuentros"][0]
    version_leida = encuentro["version"]

    # The FIRST editor works on the current version.
    primero = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            version_leida,
        ),
    )
    assert primero.status_code == 200
    assert primero.json()["data"]["version"] == version_leida + 1

    # The SECOND editor still works on the version it read and it wants a
    # DIFFERENT schedule.
    segundo = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_TARDE_ISO,
            HORA_FIN_TARDE_ISO,
            version_leida,
        ),
    )
    assert segundo.status_code == 409
    assert segundo.json()["error"]["code"] == "RESOURCE_CHANGED"

    # The conflict left NO partial effect: the schedule is the one of the
    # first editor and the version was bumped exactly once.
    lectura = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/{competencia_id}/encuentros"
    )
    assert lectura.status_code == 200
    fila = next(
        encounter
        for encounter in lectura.json()["data"]
        if encounter["id"] == encuentro["id"]
    )
    assert _a_utc(fila["inicio_programado"]) == _a_utc(HORA_INICIO_ISO)
    assert _a_utc(fila["fin_programado"]) == _a_utc(HORA_FIN_ISO)
    assert fila["version"] == version_leida + 1


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_comando_repetido_es_idempotente(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: an encounter that was already scheduled
    WHEN: the SAME command is repeated
    THEN: 200, the SAME version and NO second write
    """
    construido = await constructor_cuadro_http(3)
    encuentro = construido["encuentros"][0]
    version_leida = encuentro["version"]

    primero = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            version_leida,
        ),
    )
    assert primero.status_code == 200

    repetido = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{encuentro['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            version_leida,
        ),
    )

    assert repetido.status_code == 200
    assert repetido.json()["data"]["version"] == version_leida + 1


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_equipo_no_puede_jugar_dos_encuentros_a_la_vez(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: two encounters that share a team
    WHEN: the second one is scheduled over the first one
    THEN: 409 `EQUIPO_SOLAPADO` and the second encounter is NOT scheduled
    """
    construido = await constructor_cuadro_http(2)
    competencia_id = construido["competencia_id"]
    ronda_id = construido["rondas"][0]
    primero = construido["encuentros"][0]

    # A SECOND encounter of the same round with the SAME teams.
    gemelo = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia_id}/encuentros",
        json=make_encuentro_create_http_payload(
            ronda_id,
            2,
            construido["entradas"][0],
            construido["entradas"][1],
        ),
    )
    assert gemelo.status_code == 201
    cuerpo_gemelo = gemelo.json()["data"]

    await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{primero['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            primero["version"],
        ),
    )

    solapado = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{cuerpo_gemelo['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_SOLAPADO_ISO,
            HORA_FIN_SOLAPADO_ISO,
            cuerpo_gemelo["version"],
        ),
    )

    assert solapado.status_code == 409
    assert solapado.json()["error"]["code"] == "EQUIPO_SOLAPADO"

    # The second encounter was NOT scheduled.
    lectura = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/{competencia_id}/encuentros"
    )
    fila = next(
        encounter
        for encounter in lectura.json()["data"]
        if encounter["id"] == cuerpo_gemelo["id"]
    )
    assert fila["inicio_programado"] is None
    assert fila["fin_programado"] is None
    assert fila["estado"] == "BORRADOR"


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_encuentro_que_se_toca_no_se_solapa(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: two encounters that share a team
    WHEN: the second one starts exactly when the first one ends
    THEN: the schedule is accepted (the intervals are SEMI-OPEN)
    """
    construido = await constructor_cuadro_http(2)
    competencia_id = construido["competencia_id"]
    ronda_id = construido["rondas"][0]
    primero = construido["encuentros"][0]

    gemelo = await cliente_admin_competencias.post(
        f"{URL_ADMIN}/{competencia_id}/encuentros",
        json=make_encuentro_create_http_payload(
            ronda_id,
            2,
            construido["entradas"][0],
            construido["entradas"][1],
        ),
    )
    assert gemelo.status_code == 201
    cuerpo_gemelo = gemelo.json()["data"]

    await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{primero['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ISO,
            HORA_FIN_ISO,
            primero["version"],
        ),
    )

    # The second one TOUCHES the first one: it starts when it ends.
    encadenado = await cliente_admin_competencias.patch(
        f"{URL_ENCUENTROS}/{cuerpo_gemelo['id']}/programacion",
        json=make_programacion_http_payload(
            HORA_INICIO_ENCADENADO_ISO,
            HORA_FIN_ENCADENADO_ISO,
            cuerpo_gemelo["version"],
        ),
    )

    assert encadenado.status_code == 200
    assert encadenado.json()["data"]["estado"] == "PROGRAMADO"
