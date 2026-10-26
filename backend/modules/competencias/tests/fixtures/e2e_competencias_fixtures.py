"""
Fixtures of the END-TO-END flow of the bracket (the HTTP surface).

The E2E suite walks the flow the administrator walks in the administration:
every step of the bracket travels through the HTTP surface and NEVER through
the ORM. The client is `ninja_extra.testing.TestAsyncClient` because the
controllers are ASYNC (`contract/django-app-architecture-contract.md` §2.1).

The builders live in this module — and NOT in the `conftest.py` of the suite —
because the conftest of a test folder only LOADS the fixture modules
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3).
"""
import pytest
from asgiref.sync import sync_to_async

from modules.competencias.tests.factories import (
    make_bracket_parcial_payload,
    make_bye_http_payload,
    make_competencia_create_http_payload,
    make_competencia_equipo_create_http_payload,
    make_encuentro_create_http_payload,
    make_ronda_create_http_payload,
)

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"
URL_PUBLICA = "/competencias"


@pytest.fixture
def constructor_cuadro_http(
    cliente_admin_competencias,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
    crear_equipos_competencia,
):
    """Return an ASYNC builder of a WHOLE bracket through the HTTP surface.

    The builder does exactly what the administrator does and nothing more:

    1. it creates the competition,
    2. it registers the teams with their MANUAL order,
    3. it creates the rounds of the manual plan,
    4. it creates the encounters with the slots the administrator typed,
    5. it configures the MANUAL byes (the system never chooses one).

    The teams belong to another module (`salesianos_fest`): they are the
    PRECONDITION of the flow, so they are created in the ORM; everything the
    bracket owns is created through HTTP.

    Returns:
        A dict with the ids of everything it created: `competencia_id`,
        `competencia_version`, `entradas`, `rondas`, `encuentros` and the
        manual `plan` it followed.
    """

    async def _construir(num_equipos: int, nombre: str = "Eliminatoria E2E"):
        """Build the bracket of `num_equipos` teams through the HTTP surface."""
        equipos = await sync_to_async(crear_equipos_competencia)(num_equipos)

        creada = await cliente_admin_competencias.post(
            URL_ADMIN,
            json=make_competencia_create_http_payload(
                evento_competencia.id,
                disciplina_competencia.id,
                categoria_competencia.id,
                nombre=nombre,
            ),
        )
        assert creada.status_code == 201, creada.text
        cuerpo_competencia = creada.json()["data"]

        entradas = []
        for indice, equipo in enumerate(equipos):
            respuesta = await cliente_admin_competencias.post(
                f"{URL_ADMIN}/{cuerpo_competencia['id']}/equipos",
                json=make_competencia_equipo_create_http_payload(
                    equipo.id,
                    indice + 1,
                ),
            )
            assert respuesta.status_code == 201, respuesta.text
            entradas.append(respuesta.json()["data"]["id"])

        plan = make_bracket_parcial_payload(num_equipos)
        rondas = []
        for ronda_plan in plan["rondas"]:
            respuesta = await cliente_admin_competencias.post(
                f"{URL_ADMIN}/{cuerpo_competencia['id']}/rondas",
                json=make_ronda_create_http_payload(
                    ronda_plan["etiqueta"],
                    ronda_plan["orden"],
                ),
            )
            assert respuesta.status_code == 201, respuesta.text
            rondas.append(respuesta.json()["data"]["id"])

        encuentros = []
        for indice_ronda, ronda_plan in enumerate(plan["rondas"]):
            for encuentro_plan in ronda_plan["encuentros"]:
                participante_1 = (
                    entradas[encuentro_plan["participante_1"]]
                    if encuentro_plan["participante_1"] is not None
                    else None
                )
                participante_2 = (
                    entradas[encuentro_plan["participante_2"]]
                    if encuentro_plan["participante_2"] is not None
                    else None
                )
                respuesta = await cliente_admin_competencias.post(
                    f"{URL_ADMIN}/{cuerpo_competencia['id']}/encuentros",
                    json=make_encuentro_create_http_payload(
                        rondas[indice_ronda],
                        encuentro_plan["orden"],
                        participante_1,
                        participante_2,
                    ),
                )
                assert respuesta.status_code == 201, respuesta.text
                cuerpo = respuesta.json()["data"]

                if encuentro_plan["es_bye"]:
                    bye = await cliente_admin_competencias.post(
                        f"{URL_ENCUENTROS}/{cuerpo['id']}/bye",
                        json=make_bye_http_payload(cuerpo["version"]),
                    )
                    assert bye.status_code == 200, bye.text
                    cuerpo = bye.json()["data"]

                encuentros.append(cuerpo)

        return {
            "competencia_id": cuerpo_competencia["id"],
            "competencia_version": cuerpo_competencia["version"],
            "entradas": entradas,
            "rondas": rondas,
            "encuentros": encuentros,
            "plan": plan,
            "equipos": equipos,
        }

    return _construir
