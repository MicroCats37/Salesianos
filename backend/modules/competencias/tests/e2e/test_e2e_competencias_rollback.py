"""
E2E — the ROLLBACK of a deployment that already used the bracket.

The design fixes the rollback of the module in two steps:

- BEFORE the use, the rollback reverts the migration,
- AFTER the use, the rollback DISABLES the writes and the navigation and it
  keeps the tables in READ-ONLY: the history is never deleted.

This file proves the SECOND half — the one the code is responsible for:

1. a competition that is already in use CANNOT be physically deleted
   (409 `DELETE_NOT_ALLOWED`): the rollback never destroys the data,
2. the bracket stays READABLE after the rollback (the administrative AND the
   public surfaces keep serving it),
3. the rollback of a used competition is a CANCELLATION: it is terminal and
   auditable, and the data is still readable afterwards,
4. the audit history survives the rollback and it GROWS with the
   cancellation.
"""
import pytest
from asgiref.sync import sync_to_async

from modules.competencias.domain.models import Competencia, Encuentro
from modules.competencias.tests.factories import (
    make_estado_competencia_http_payload,
)

URL_ADMIN = "/administracion/competencias"
URL_ENCUENTROS = f"{URL_ADMIN}/encuentros"
URL_PUBLICA = "/competencias"


def _historial_de_competencia(competencia_id) -> int:
    """Return how many historical records the competition has."""
    return Competencia.objects.get(id=competencia_id).history.count()


def _historial_de_encuentro(encuentro_id) -> int:
    """Return how many historical records the encounter has."""
    return Encuentro.objects.get(id=encuentro_id).history.count()


@pytest.mark.django_db(transaction=True)
async def test_e2e_un_despliegue_revertido_no_borra_el_cuadro_en_uso(
    cliente_admin_competencias,
    cliente_api_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: a competition that is already in use
    WHEN: the deployment is reverted (the physical delete is attempted)
    THEN: 409 `DELETE_NOT_ALLOWED` and the bracket is STILL readable
    """
    construido = await constructor_cuadro_http(3)
    competencia_id = construido["competencia_id"]

    borrado = await cliente_admin_competencias.delete(f"{URL_ADMIN}/{competencia_id}")

    assert borrado.status_code == 409
    assert borrado.json()["error"]["code"] == "DELETE_NOT_ALLOWED"

    # The data stays READABLE: the administrative surface keeps serving it.
    admin = await cliente_admin_competencias.get(
        f"{URL_ADMIN}/{competencia_id}/cuadro"
    )
    assert admin.status_code == 200
    assert admin.json()["data"]["total_equipos"] == 3

    # ... and the PUBLIC surface keeps serving it too.
    publico = await cliente_api_competencias.get(
        f"{URL_PUBLICA}/{competencia_id}/cuadro"
    )
    assert publico.status_code == 200
    assert publico.json()["data"]["total_equipos"] == 3


@pytest.mark.django_db(transaction=True)
async def test_e2e_el_revertido_de_un_cuadro_en_uso_es_una_cancelacion_auditada(
    cliente_admin_competencias,
    cliente_api_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: a competition that is already in use
    WHEN: the rollback is applied as a cancellation
    THEN: the competition is CANCELADA (terminal) and its bracket is STILL
    readable — the tables stay in read-only and the history is intact
    """
    construido = await constructor_cuadro_http(3)
    competencia_id = construido["competencia_id"]

    historial_inicial = await sync_to_async(_historial_de_competencia)(competencia_id)

    cancelada = await cliente_admin_competencias.patch(
        f"{URL_ADMIN}/{competencia_id}/estado",
        json=make_estado_competencia_http_payload(
            "CANCELADA",
            construido["competencia_version"],
        ),
    )

    assert cancelada.status_code == 200
    assert cancelada.json()["data"]["estado"] == "CANCELADA"

    # The data is STILL readable after the rollback.
    sigue = await cliente_api_competencias.get(
        f"{URL_PUBLICA}/{competencia_id}/cuadro"
    )
    assert sigue.status_code == 200
    assert sigue.json()["data"]["total_equipos"] == 3

    # The history is NEVER deleted: it grew with the cancellation.
    historial_final = await sync_to_async(_historial_de_competencia)(competencia_id)
    assert historial_final > historial_inicial


@pytest.mark.django_db(transaction=True)
async def test_e2e_los_encuentros_de_un_cuadro_revertido_no_se_borran(
    cliente_admin_competencias,
    constructor_cuadro_http,
):
    """
    GIVEN: a bracket whose encounters are already in use
    WHEN: the rollback tries to delete them
    THEN: 409 `DELETE_NOT_ALLOWED` and the encounters keep their history
    """
    construido = await constructor_cuadro_http(3)
    encuentro = construido["encuentros"][0]

    historial_inicial = await sync_to_async(_historial_de_encuentro)(
        encuentro["id"]
    )

    borrado = await cliente_admin_competencias.delete(
        f"{URL_ENCUENTROS}/{encuentro['id']}"
    )

    assert borrado.status_code == 409
    assert borrado.json()["error"]["code"] == "DELETE_NOT_ALLOWED"

    historial_final = await sync_to_async(_historial_de_encuentro)(encuentro["id"])
    assert historial_final == historial_inicial
