"""El recorrido HTTP de la consola de validación.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0`

GIVEN  un operador con la capacidad de acreditaciones
WHEN   llama a las dos rutas de la consola
THEN   recibe el envelope congelado y el canje queda registrado.

El cliente es `django.test.Client`: los controllers son async y este cliente
lo soporta (`FREEZE-TC-1.0.0`).
"""

import pytest
from ninja_jwt.tokens import AccessToken

from modules.validaciones.domain.models import ValidacionTicket

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("modules.validaciones.tests.urls_validaciones"),
]


@pytest.fixture
def cabeceras(db, usuario_admin):
    """La cabecera de autorización del operador."""
    token = AccessToken.for_user(usuario_admin)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_sin_sesion_la_comprobacion_responde_401(client, ticket_entrada):
    """GIVEN una petición sin cuenta · WHEN se comprueba · THEN 401."""
    respuesta = client.post(
        "/api/validaciones/preview",
        data={"codigo": ticket_entrada.codigo},
        content_type="application/json",
    )
    assert respuesta.status_code == 401


def test_sin_capacidad_la_comprobacion_responde_403(
    client, usuario_responsable, ticket_entrada
):
    """GIVEN una cuenta sin la capacidad · WHEN se comprueba · THEN 403.

    El grupo autoriza a OPERAR; el derecho autoriza a ingresar
    (`contratos/02` §6).
    """
    token = AccessToken.for_user(usuario_responsable)
    respuesta = client.post(
        "/api/validaciones/preview",
        data={"codigo": ticket_entrada.codigo},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert respuesta.status_code == 403


def test_la_comprobacion_devuelve_el_envelope_congelado(
    client, cabeceras, ticket_entrada
):
    """GIVEN un operador · WHEN comprueba una credencial · THEN el envelope
    de éxito con la forma congelada de `FR-05` §3.1."""
    respuesta = client.post(
        "/api/validaciones/preview",
        data={"codigo": ticket_entrada.codigo},
        content_type="application/json",
        **cabeceras,
    )
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None

    data = cuerpo["data"]
    assert data["tipo_derecho"] == "PASE"
    assert data["puede_canjear"] is True
    assert data["cantidad_total"] == 1
    assert data["cantidad_disponible"] == 1
    assert data["cantidad_consumida"] == 0
    assert data["motivo_codigo"] is None
    assert "persona_id" in data["titular"]
    assert "nombre" in data["titular"]
    # La credencial NO vuelve en la respuesta: es un secreto.
    assert ticket_entrada.codigo not in respuesta.content.decode("utf-8")


def test_una_credencial_inexistente_responde_404(client, cabeceras):
    """GIVEN un código que no existe · WHEN se comprueba · THEN 404."""
    respuesta = client.post(
        "/api/validaciones/preview",
        data={"codigo": "FEST-NO-EXISTE"},
        content_type="application/json",
        **cabeceras,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "TICKET_NO_ENCONTRADO"


def test_la_confirmacion_canjea_y_deja_acta(client, cabeceras, ticket_entrada):
    """GIVEN un operador · WHEN confirma · THEN el acta queda registrada."""
    respuesta = client.post(
        "/api/validaciones/confirmar",
        data={
            "codigo": ticket_entrada.codigo,
            "idempotency_key": "clave-e2e-1",
        },
        content_type="application/json",
        **cabeceras,
    )
    assert respuesta.status_code == 201

    data = respuesta.json()["data"]
    assert data["cantidad_consumida"] == 1
    assert data["cantidad_restante"] == 0
    assert data["repetido"] is False

    assert ValidacionTicket.objects.count() == 1


def test_la_repeticion_con_la_misma_clave_devuelve_el_mismo_canje(
    client, cabeceras, ticket_entrada
):
    """GIVEN un canje hecho · WHEN se repite la clave · THEN el mismo acta."""
    cuerpo = {
        "codigo": ticket_entrada.codigo,
        "idempotency_key": "clave-e2e-2",
    }
    primera = client.post(
        "/api/validaciones/confirmar",
        data=cuerpo,
        content_type="application/json",
        **cabeceras,
    )
    segunda = client.post(
        "/api/validaciones/confirmar",
        data=cuerpo,
        content_type="application/json",
        **cabeceras,
    )

    assert primera.status_code == 201
    assert segunda.status_code == 201
    assert (
        primera.json()["data"]["validacion_id"]
        == segunda.json()["data"]["validacion_id"]
    )
    assert segunda.json()["data"]["repetido"] is True
    assert ValidacionTicket.objects.count() == 1


def test_el_segundo_canje_con_otra_clave_responde_409(
    client, cabeceras, ticket_entrada
):
    """GIVEN un ticket ya canjeado · WHEN se canjea con otra clave · THEN 409."""
    client.post(
        "/api/validaciones/confirmar",
        data={"codigo": ticket_entrada.codigo, "idempotency_key": "clave-e2e-3"},
        content_type="application/json",
        **cabeceras,
    )
    respuesta = client.post(
        "/api/validaciones/confirmar",
        data={"codigo": ticket_entrada.codigo, "idempotency_key": "clave-e2e-4"},
        content_type="application/json",
        **cabeceras,
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "TICKET_YA_CONSUMIDO"
