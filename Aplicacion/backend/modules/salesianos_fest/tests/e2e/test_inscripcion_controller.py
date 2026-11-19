"""Superficie HTTP de las inscripciones y del catálogo.

GIVEN  una cuenta autenticada, un catálogo y un paquete vigente
WHEN   se crea la inscripción inicial y se consultan el catálogo, el detalle
       y los equipos
THEN   responde el envelope congelado con los códigos de error estables, y
       la autorización se decide en el backend (`RN-A02`, `FR-01`).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json
from decimal import Decimal

import pytest
from django.test import Client

pytestmark = [
    pytest.mark.urls("modules.salesianos_fest.tests.urls_salesianos_fest"),
    pytest.mark.django_db,
]


@pytest.fixture
def cliente():
    """Cliente HTTP de prueba."""
    return Client()


def _autorizacion(usuario) -> dict:
    """El header `Authorization` del usuario indicado."""
    from ninja_jwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(usuario).access_token)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _payload_alta(edicion_id, paquete_id, disciplina_id) -> dict:
    """El payload del alta de la inscripción inicial."""
    return {
        "edicion_id": str(edicion_id),
        "paquete_id": str(paquete_id),
        "equipos": [
            {"disciplina_id": str(disciplina_id), "nombre": "EquipoUno"},
        ],
    }


# ── RT-IN-14 · Alta de la inscripción inicial ───────────────────────────────


def test_el_alta_devuelve_la_inscripcion_y_su_compra_pendiente(
    cliente, usuario_responsable, edicion_publicada, paquete, disciplina, precio
):
    """GIVEN una cuenta con persona y un paquete vigente
    WHEN  confirma el alta
    THEN  responde 201 con la inscripción, la compra PENDIENTE y la causa
       operativa; los cupos pagados son CERO (`RN-I02`).
    """
    respuesta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(_payload_alta(edicion_publicada.id, paquete.id, disciplina.id)),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 201
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["causa_operativa"] == "INSCRIPCION_CREADA"

    inscripcion = cuerpo["data"]["inscripcion"]
    assert inscripcion["edicion_id"] == str(edicion_publicada.id)
    assert inscripcion["paquete_id"] == str(paquete.id)
    assert inscripcion["cupos_pagados"] == 0
    assert inscripcion["cupos_disponibles"] == 0
    assert len(inscripcion["equipos"]) == 1
    assert inscripcion["equipos"][0]["disciplina_nombre"] == disciplina.nombre

    compra = cuerpo["data"]["compra"]
    assert compra["estado"] == "PENDIENTE"
    # El monto viaja como `Decimal`: el backend lo congela con dos decimales.
    # La forma exacta del número en el wire (número o cadena) es una decisión
    # pendiente del catálogo público de A0 (divergencia `D-DOM-01-01`); el
    # test comprueba el VALOR, no la forma.
    assert Decimal(str(compra["total"])) == Decimal("2500.00")
    assert compra["moneda"] == "PEN"


def test_el_alta_repetida_devuelve_la_misma_inscripcion(
    cliente, usuario_responsable, edicion_publicada, paquete, disciplina, precio
):
    """GIVEN una inscripción ya creada
    WHEN  se repite el alta
    THEN  responde 201 con la MISMA inscripción y la causa de reutilización.
    """
    payload = _payload_alta(edicion_publicada.id, paquete.id, disciplina.id)
    cabeceras = _autorizacion(usuario_responsable)

    primera = cliente.post(
        "/api/inscripciones",
        data=json.dumps(payload),
        content_type="application/json",
        **cabeceras,
    )
    segunda = cliente.post(
        "/api/inscripciones",
        data=json.dumps(payload),
        content_type="application/json",
        **cabeceras,
    )

    assert primera.status_code == 201
    assert segunda.status_code == 201
    cuerpo_primera = json.loads(primera.content)["data"]
    cuerpo_segunda = json.loads(segunda.content)["data"]
    assert (
        cuerpo_primera["inscripcion"]["id"] == cuerpo_segunda["inscripcion"]["id"]
    )
    assert cuerpo_segunda["causa_operativa"] == "INSCRIPCION_REUTILIZADA"


def test_el_alta_sin_sesion_es_401(
    cliente, edicion_publicada, paquete, disciplina
):
    """GIVEN una petición sin sesión
    WHEN  confirma el alta
    THEN  responde 401: la autenticación va antes que la autorización.
    """
    respuesta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(_payload_alta(edicion_publicada.id, paquete.id, disciplina.id)),
        content_type="application/json",
    )

    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_el_alta_de_una_disciplina_no_permitida_es_422(
    cliente, usuario_responsable, edicion_publicada, paquete, disciplina_otra_edicion, precio
):
    """GIVEN una disciplina que el paquete NO permite
    WHEN  confirma el alta
    THEN  responde 422 con el código estable `DISCIPLINA_NO_PERMITIDA`.
    """
    respuesta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(
            _payload_alta(
                edicion_publicada.id,
                paquete.id,
                disciplina_otra_edicion.id,
            )
        ),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "DISCIPLINA_NO_PERMITIDA"


# ── RT-IN-02 / RT-IN-04 · Lectura de la inscripción ─────────────────────────


def test_el_responsable_consulta_el_detalle_y_los_equipos(
    cliente, usuario_responsable, edicion_publicada, paquete, disciplina, precio
):
    """GIVEN una inscripción creada por el responsable
    WHEN  consulta su detalle y sus equipos
    THEN  ambos responden 200 con el envelope congelado.
    """
    alta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(_payload_alta(edicion_publicada.id, paquete.id, disciplina.id)),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )
    inscripcion_id = json.loads(alta.content)["data"]["inscripcion"]["id"]

    detalle = cliente.get(
        f"/api/inscripciones/{inscripcion_id}",
        **_autorizacion(usuario_responsable),
    )
    equipos = cliente.get(
        f"/api/inscripciones/{inscripcion_id}/equipos",
        **_autorizacion(usuario_responsable),
    )

    assert detalle.status_code == 200
    assert equipos.status_code == 200
    cuerpo_equipos = json.loads(equipos.content)["data"]
    assert cuerpo_equipos["inscripcion_id"] == inscripcion_id
    assert len(cuerpo_equipos["equipos"]) == 1


def test_otro_actor_no_puede_consultar_la_inscripcion(
    cliente, usuario_responsable, usuario_ajeno, edicion_publicada, paquete, disciplina, precio
):
    """GIVEN la inscripción de OTRA persona
    WHEN  un tercero la consulta
    THEN  responde 403 con `INSCRIPCION_NO_AUTORIZADA`.
    """
    alta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(_payload_alta(edicion_publicada.id, paquete.id, disciplina.id)),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )
    inscripcion_id = json.loads(alta.content)["data"]["inscripcion"]["id"]

    respuesta = cliente.get(
        f"/api/inscripciones/{inscripcion_id}",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "INSCRIPCION_NO_AUTORIZADA"


# ── RT-IN-12 / RT-IN-13 · Catálogo público ─────────────────────────────────


def test_el_catalogo_de_paquetes_es_publico_y_real(
    cliente, edicion_publicada, paquete, disciplina, precio, beneficio
):
    """GIVEN un catálogo con precio vigente
    WHEN  se consulta el catálogo público
    THEN  responde 200 con el paquete y SU precio, sin precio inventado.
    """
    respuesta = cliente.get(f"/api/catalogo/paquetes?edicion_id={edicion_publicada.id}")

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["data"]["edicion_id"] == str(edicion_publicada.id)
    assert len(cuerpo["data"]["paquetes"]) == 1
    assert Decimal(str(cuerpo["data"]["paquetes"][0]["precio"]["monto"])) == Decimal(
        "250.00"
    )


def test_el_catalogo_de_paquetes_no_inventa_precios(
    cliente, edicion_publicada, paquete_sin_precio, disciplina
):
    """GIVEN un paquete SIN precio vigente
    WHEN  se consulta el catálogo
    THEN  no aparece: el catálogo no inventa un precio de reserva.
    """
    respuesta = cliente.get(f"/api/catalogo/paquetes?edicion_id={edicion_publicada.id}")

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["data"]["paquetes"] == []


def test_el_catalogo_de_disciplinas_es_publico(
    cliente, edicion_publicada, disciplina
):
    """GIVEN una disciplina activa
    WHEN  se consulta el catálogo de disciplinas
    THEN  responde 200 con la disciplina de esa edición.
    """
    respuesta = cliente.get(
        f"/api/catalogo/disciplinas?edicion_id={edicion_publicada.id}"
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert [publicada["nombre"] for publicada in cuerpo["data"]["disciplinas"]] == [
        "Vóley Mixto"
    ]


def test_la_respuesta_no_expone_identificadores_internos(
    cliente, usuario_responsable, edicion_publicada, paquete, disciplina, precio
):
    """El envelope público no filtra trazas ni texto crudo (FR-01 §4)."""
    respuesta = cliente.post(
        "/api/inscripciones",
        data=json.dumps(_payload_alta(edicion_publicada.id, paquete.id, disciplina.id)),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    contenido = respuesta.content.decode("utf-8")
    assert respuesta.status_code == 201
    assert "Traceback" not in contenido
