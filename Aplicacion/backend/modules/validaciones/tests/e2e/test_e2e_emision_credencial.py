"""La EMISIÓN de la credencial por HTTP: el envelope, los permisos y el secreto.

GIVEN  un operador con la capacidad de acreditaciones y un derecho de entrada
WHEN   emite su credencial
THEN   responde 201 con el envelope congelado, el código se entrega UNA vez y
       una segunda emisión se rechaza con 409 (`RT-RT-04`).

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
    pytest.mark.urls("modules.validaciones.tests.urls_validaciones"),
]


@pytest.fixture
def cabeceras(db, usuario_admin):
    """La cabecera de autorización del operador."""
    token = AccessToken.for_user(usuario_admin)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def derecho_de_cortesia(cortesia_pase):
    """El derecho de entrada de la cortesía de prueba."""
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    return PaseBeneficiario.objects.get(cortesia=cortesia_pase)


def _emitir(client, cabeceras, derecho_id):
    """La petición de emisión de la credencial."""
    return client.post(
        "/api/validaciones/tickets",
        data=json.dumps({"derecho_id": str(derecho_id)}),
        content_type="application/json",
        **cabeceras,
    )


# ── La emisión ──────────────────────────────────────────────────────────────


def test_la_emision_responde_201_con_el_envelope_congelado(
    client, cabeceras, derecho_de_cortesia
):
    """GIVEN un operador · WHEN emite la credencial · THEN 201 con la forma
    congelada: el tipo lo DERIVA el dueño del derecho."""
    respuesta = _emitir(client, cabeceras, derecho_de_cortesia.id)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["message"] == "Credencial emitida correctamente."

    datos = cuerpo["data"]
    assert datos["tipo_derecho"] == "ENTRADA_CORTESIA"
    assert datos["operacion"] == "INGRESO"
    assert datos["codigo"].startswith("FEST-")
    assert datos["ticket_id"]
    assert datos["edicion_id"]
    assert datos["emitido_en"]


def test_la_emision_devuelve_el_codigo_una_sola_vez(
    client, cabeceras, derecho_de_cortesia
):
    """GIVEN un operador · WHEN emite la credencial · THEN el código se
    entrega en ESTA respuesta y en ninguna otra."""
    respuesta = _emitir(client, cabeceras, derecho_de_cortesia.id)
    codigo = respuesta.json()["data"]["codigo"]

    # La puerta NO devuelve el código: lo recibe, no lo publica.
    comprobacion = client.post(
        "/api/validaciones/preview",
        data=json.dumps({"codigo": codigo}),
        content_type="application/json",
        **cabeceras,
    )
    assert comprobacion.status_code == 200
    assert codigo not in comprobacion.content.decode("utf-8")


def test_la_credencial_emitida_escanable_en_la_puerta(
    client, cabeceras, derecho_de_cortesia
):
    """GIVEN una credencial emitida
    WHEN  se comprueba y se confirma en la puerta
    THEN  se puede canjear: la emisión no rompe el flujo de la consola."""
    emission = _emitir(client, cabeceras, derecho_de_cortesia.id)
    codigo = emission.json()["data"]["codigo"]

    comprobacion = client.post(
        "/api/validaciones/preview",
        data=json.dumps({"codigo": codigo}),
        content_type="application/json",
        **cabeceras,
    )
    assert comprobacion.status_code == 200
    assert comprobacion.json()["data"]["tipo_derecho"] == "ENTRADA_CORTESIA"
    assert comprobacion.json()["data"]["puede_canjear"] is True

    confirmacion = client.post(
        "/api/validaciones/confirmar",
        data=json.dumps(
            {"codigo": codigo, "idempotency_key": "clave-de-prueba-emision"}
        ),
        content_type="application/json",
        **cabeceras,
    )
    assert confirmacion.status_code == 201
    assert confirmacion.json()["data"]["cantidad_consumida"] == 1


# ── Los errores ─────────────────────────────────────────────────────────────


def test_sin_sesion_la_emision_responde_401(client, derecho_de_cortesia):
    """GIVEN una petición sin cuenta · WHEN emite · THEN 401."""
    respuesta = client.post(
        "/api/validaciones/tickets",
        data=json.dumps({"derecho_id": str(derecho_de_cortesia.id)}),
        content_type="application/json",
    )
    assert respuesta.status_code == 401


def test_sin_capacidad_la_emision_responde_403(
    client, usuario_responsable, derecho_de_cortesia
):
    """GIVEN una cuenta sin la capacidad · WHEN emite · THEN 403."""
    token = AccessToken.for_user(usuario_responsable)
    respuesta = client.post(
        "/api/validaciones/tickets",
        data=json.dumps({"derecho_id": str(derecho_de_cortesia.id)}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert respuesta.status_code == 403


def test_un_derecho_inexistente_responde_404(client, cabeceras):
    """GIVEN un derecho que no existe · WHEN emite · THEN 404 con el código
    estable."""
    from uuid import uuid4

    respuesta = _emitir(client, cabeceras, uuid4())

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "PASE_BENEFICIARIO_NO_ENCONTRADO"


def test_la_segunda_emision_del_mismo_derecho_responde_409(
    client, cabeceras, derecho_de_cortesia
):
    """GIVEN un derecho con una credencial vigente · WHEN emite OTRA · THEN 409.

    La credencial es ONE-SHOT por derecho: dos códigos vivos para la misma
    persona duplicarían el acceso.
    """
    primera = _emitir(client, cabeceras, derecho_de_cortesia.id)
    assert primera.status_code == 201

    segunda = _emitir(client, cabeceras, derecho_de_cortesia.id)

    assert segunda.status_code == 409
    assert segunda.json()["error"]["code"] == "CONFLICT"


def test_sin_derecho_no_se_emite(client, cabeceras):
    """GIVEN una petición sin `derecho_id` · WHEN emite · THEN 422."""
    respuesta = client.post(
        "/api/validaciones/tickets",
        data=json.dumps({}),
        content_type="application/json",
        **cabeceras,
    )
    assert respuesta.status_code == 422
