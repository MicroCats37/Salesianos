"""La REVOCACIÓN de una cortesía por HTTP: el envelope, el permiso y la
idempotencia.

GIVEN  un administrador y una cortesía ACTIVA
WHEN   se revoca con un motivo
THEN   responde 200 con el envelope congelado, la repetición NO es un error y
       una cortesía inexistente responde 404 (`RT-PS-09`).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).

Change: `administracion-pases-alta-directa` · Apply C
"""

import json

import pytest
from ninja_jwt.tokens import AccessToken

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("modules.salesianos_fest.tests.urls_salesianos_fest"),
]


@pytest.fixture
def cabeceras(db, usuario_admin):
    """La cabecera de autorización del administrador."""
    token = AccessToken.for_user(usuario_admin)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _revocar(client, cabeceras, cortesia_id, motivo="Solicitud del beneficiario."):
    """La petición de revocación de una cortesía."""
    return client.post(
        f"/api/administracion/pases/cortesias/{cortesia_id}/revocar",
        data=json.dumps({"motivo": motivo}),
        content_type="application/json",
        **cabeceras,
    )


# ── La revocación ───────────────────────────────────────────────────────────


def test_la_revocacion_responde_200_con_el_envelope_congelado(
    client, cabeceras, cortesia_pase
):
    """GIVEN un administrador · WHEN revoca · THEN 200 con el acta revocada."""
    respuesta = _revocar(client, cabeceras, cortesia_pase.id)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["message"] == "Cortesía revocada correctamente."

    datos = cuerpo["data"]
    assert datos["id"] == str(cortesia_pase.id)
    assert datos["estado"] == "REVOCADA"
    assert datos["motivo_revocacion"] == "Solicitud del beneficiario."
    assert datos["ya_revocado"] is False
    assert datos["revocado_en"]


def test_la_revocacion_repetida_responde_200_con_ya_revocado(
    client, cabeceras, cortesia_pase
):
    """GIVEN una cortesía ya revocada · WHEN se revoca OTRA vez · THEN 200 con
    `ya_revocado=true`: la repetición NO es un error."""
    _revocar(client, cabeceras, cortesia_pase.id)

    repetida = _revocar(client, cabeceras, cortesia_pase.id)

    assert repetida.status_code == 200
    assert repetida.json()["data"]["ya_revocado"] is True
    assert repetida.json()["data"]["estado"] == "REVOCADA"


def test_la_cortesia_revocada_no_aparece_como_activa(
    client, cabeceras, cortesia_pase, edicion_con_pases
):
    """GIVEN una cortesía revocada · WHEN se lista · THEN el estado es
    `REVOCADA`: la revocación es AUDITADA, no un borrado."""
    _revocar(client, cabeceras, cortesia_pase.id)

    listado = client.get(
        f"/api/administracion/pases/cortesias?edicion_id={edicion_con_pases.id}",
        **cabeceras,
    )

    assert listado.status_code == 200
    filas = listado.json()["data"]["items"]
    assert len(filas) == 1
    assert filas[0]["estado"] == "REVOCADA"


# ── Los errores ─────────────────────────────────────────────────────────────


def test_sin_motivo_la_revocacion_responde_422(client, cabeceras, cortesia_pase):
    """GIVEN una revocación sin motivo · WHEN revoca · THEN 422 con el código
    estable: sin motivo no hay auditoría."""
    respuesta = _revocar(client, cabeceras, cortesia_pase.id, motivo="")

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "CORTESIA_MOTIVO_INVALIDO"


def test_una_cortesia_inexistente_responde_404(client, cabeceras):
    """GIVEN un acta que no existe · WHEN revoca · THEN 404 con el código
    estable."""
    from uuid import uuid4

    respuesta = _revocar(client, cabeceras, uuid4())

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "CORTESIA_NO_ENCONTRADA"


def test_sin_sesion_la_revocacion_responde_401(client, cortesia_pase):
    """GIVEN una petición sin cuenta · WHEN revoca · THEN 401."""
    respuesta = client.post(
        f"/api/administracion/pases/cortesias/{cortesia_pase.id}/revocar",
        data=json.dumps({"motivo": "Solicitud del beneficiario."}),
        content_type="application/json",
    )
    assert respuesta.status_code == 401


def test_sin_autorizacion_la_revocacion_responde_403(
    client, usuario_responsable, cortesia_pase
):
    """GIVEN una cuenta sin la capacidad de administrador · WHEN revoca · THEN
    403."""
    token = AccessToken.for_user(usuario_responsable)
    respuesta = client.post(
        f"/api/administracion/pases/cortesias/{cortesia_pase.id}/revocar",
        data=json.dumps({"motivo": "Solicitud del beneficiario."}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert respuesta.status_code == 403
