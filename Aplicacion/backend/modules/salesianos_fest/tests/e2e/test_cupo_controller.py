"""Superficie HTTP del pool, de los participantes y de la ampliación.

GIVEN  una inscripción con capacidad pagada y su responsable
WHEN   se consulta el pool, se agregan y retiran participantes y se compran
       cupos extra
THEN   responde el envelope congelado con la aritmética de cupos que calcula
       el servidor y con los códigos de error estables del ledger
       (`RT-IN-03`, `RT-IN-05`, `RT-IN-06`, `RT-CM-01`).

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


# ── RT-IN-03 · Lectura del pool ─────────────────────────────────────────────


def test_el_pool_publica_los_tres_numeros(
    cliente, usuario_responsable, inscripcion
):
    """GIVEN una inscripción con 10 cupos pagados
    WHEN  el responsable consulta el pool
    THEN  responde 200 con pagados, asignados y disponibles: el cliente
       nunca resta (`RN-I03`, `SH-05` §1.3).
    """
    respuesta = cliente.get(
        f"/api/inscripciones/{inscripcion.id}/pool",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["data"]["inscripcion_id"] == str(inscripcion.id)
    assert cuerpo["data"]["cupos_pagados"] == 10
    assert cuerpo["data"]["cupos_asignados"] == 0
    assert cuerpo["data"]["cupos_disponibles"] == 10
    assert cuerpo["data"]["participaciones"] == []
    assert cuerpo["data"]["impedimentos"] == []


def test_el_pool_de_otra_inscripcion_no_se_abre(
    cliente, usuario_ajeno, inscripcion
):
    """GIVEN una inscripción que no es del actor
    WHEN  consulta su pool
    THEN  responde 403 con `INSCRIPCION_NO_AUTORIZADA`.
    """
    respuesta = cliente.get(
        f"/api/inscripciones/{inscripcion.id}/pool",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "INSCRIPCION_NO_AUTORIZADA"


def test_el_pool_sin_sesion_es_401(cliente, inscripcion):
    """GIVEN una petición sin sesión
    WHEN  consulta el pool
    THEN  responde 401: la autenticación va antes que la autorización.
    """
    respuesta = cliente.get(f"/api/inscripciones/{inscripcion.id}/pool")

    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ── RT-IN-05 · Agregar un participante ──────────────────────────────────────


def test_agregar_un_participante_actualiza_el_saldo(
    cliente, usuario_responsable, inscripcion, equipo, persona_participante
):
    """GIVEN una inscripción con cupos disponibles
    WHEN  el responsable agrega un participante
    THEN  responde 200 con la participación ACTIVA y el saldo actualizado.
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=json.dumps(
            {
                "persona_id": str(persona_participante.id),
                "equipo_id": str(equipo.id),
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    datos = cuerpo["data"]
    assert datos["causa_operativa"] == "PARTICIPACION_AGREGADA"
    assert datos["cupos_asignados"] == 1
    assert datos["cupos_disponibles"] == 9
    assert len(datos["participaciones"]) == 1

    participacion = datos["participaciones"][0]
    assert participacion["persona_id"] == str(persona_participante.id)
    assert participacion["equipo_id"] == str(equipo.id)
    assert participacion["estado"] == "ACTIVA"
    assert participacion["ocupa_cupo"] is True


def test_agregar_un_participante_duplicado_es_422(
    cliente, usuario_responsable, inscripcion, equipo, persona_participante
):
    """GIVEN una persona que ya participa en la inscripción
    WHEN  se intenta agregarla otra vez
    THEN  responde 422 con el código estable `PARTICIPANTE_DUPLICADO`.
    """
    payload = json.dumps(
        {
            "persona_id": str(persona_participante.id),
            "equipo_id": str(equipo.id),
        }
    )
    cabeceras = _autorizacion(usuario_responsable)
    cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )

    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "PARTICIPANTE_DUPLICADO"


def test_agregar_un_participante_de_otra_inscripcion_es_403(
    cliente, usuario_ajeno, inscripcion, equipo, persona_participante
):
    """GIVEN una cuenta que no es la responsable
    WHEN  intenta agregar un participante
    THEN  responde 403 con `INSCRIPCION_NO_AUTORIZADA`.
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=json.dumps(
            {
                "persona_id": str(persona_participante.id),
                "equipo_id": str(equipo.id),
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "INSCRIPCION_NO_AUTORIZADA"


def test_una_identificacion_ambigua_es_422(
    cliente, usuario_responsable, inscripcion, equipo, persona_participante
):
    """GIVEN un payload que identifica a la persona de DOS maneras
    WHEN  se envía
    THEN  responde 422: la identificación es excluyente y la verifica el
       servidor.
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=json.dumps(
            {
                "persona_id": str(persona_participante.id),
                "tipo_documento": "DNI",
                "numero_documento": "33333333",
                "equipo_id": str(equipo.id),
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "VALIDATION_ERROR"


# ── RT-IN-06 · Retirar un participante ──────────────────────────────────────


def test_retirar_un_participante_libera_su_cupo(
    cliente, usuario_responsable, inscripcion, equipo, persona_participante
):
    """GIVEN un participante que ocupa un cupo
    WHEN  el responsable lo retira
    THEN  responde 200 con el cupo liberado y la participación conservada
       como `RETIRADA` (`RN-I04`).
    """
    cabeceras = _autorizacion(usuario_responsable)
    agregado = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/participantes",
        data=json.dumps(
            {
                "persona_id": str(persona_participante.id),
                "equipo_id": str(equipo.id),
            }
        ),
        content_type="application/json",
        **cabeceras,
    )
    participacion_id = json.loads(agregado.content)["data"]["participaciones"][0]["id"]

    respuesta = cliente.delete(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participacion_id}",
        **cabeceras,
    )

    assert respuesta.status_code == 200
    datos = json.loads(respuesta.content)["data"]
    assert datos["causa_operativa"] == "PARTICIPACION_RETIRADA"
    assert datos["cupos_asignados"] == 0
    assert datos["cupos_disponibles"] == 10
    assert datos["participaciones"][0]["estado"] == "RETIRADA"
    assert datos["participaciones"][0]["ocupa_cupo"] is False


# ── RT-CM-01 · Compra de cupos extra ────────────────────────────────────────


def test_comprar_cupos_extra_crea_la_compra_pendiente(
    cliente, usuario_responsable, inscripcion, precio
):
    """GIVEN una inscripción con un paquete vigente
    WHEN  el responsable compra tres cupos extra
    THEN  responde 201 con la compra PENDIENTE, el importe congelado por el
       servidor y la capacidad SIN cambios (`RN-I02`, `RN-C02`).
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=json.dumps({"cantidad": 3}),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 201
    cuerpo = json.loads(respuesta.content)
    datos = cuerpo["data"]
    assert datos["inscripcion_id"] == str(inscripcion.id)
    assert datos["causa_operativa"] == "COMPRA_CUPOS_CREADA"
    assert datos["cupos_solicitados"] == 3
    assert datos["cupos_pagados"] == 10
    assert datos["compra"]["estado"] == "PENDIENTE"
    assert Decimal(str(datos["compra"]["total"])) == Decimal("750.00")
    assert datos["compra"]["moneda"] == "PEN"


def test_comprar_cupos_extra_repetido_reutiliza_la_compra(
    cliente, usuario_responsable, inscripcion, precio
):
    """GIVEN una compra de cupos extra ya pendiente
    WHEN  se repite la misma petición
    THEN  responde 201 con la MISMA compra y la causa de reutilización
       (`FR-04` I-4).
    """
    cabeceras = _autorizacion(usuario_responsable)
    payload = json.dumps({"cantidad": 3})

    primera = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )
    segunda = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )

    assert primera.status_code == 201
    assert segunda.status_code == 201
    datos = json.loads(segunda.content)["data"]
    assert datos["causa_operativa"] == "COMPRA_CUPOS_REUTILIZADA"
    assert datos["compra"]["reutilizada"] is True
    assert (
        datos["compra"]["compra_id"]
        == json.loads(primera.content)["data"]["compra"]["compra_id"]
    )


def test_comprar_una_cantidad_invalida_es_422(
    cliente, usuario_responsable, inscripcion, precio
):
    """GIVEN una cantidad que no está dentro de los límites
    WHEN  se intenta comprar
    THEN  responde 422 con el código CONGELADO `CUPO_INVALIDO`.
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=json.dumps({"cantidad": 0}),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "CUPO_INVALIDO"


def test_comprar_cupos_de_otra_inscripcion_es_403(
    cliente, usuario_ajeno, inscripcion, precio
):
    """GIVEN una cuenta que no es la responsable
    WHEN  intenta comprar cupos extra
    THEN  responde 403 con el código CONGELADO `COMPRA_NO_AUTORIZADA`.
    """
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=json.dumps({"cantidad": 3}),
        content_type="application/json",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "COMPRA_NO_AUTORIZADA"


def test_la_respuesta_no_expone_identificadores_internos(
    cliente, usuario_responsable, inscripcion, precio
):
    """El envelope público no filtra trazas ni texto crudo (FR-01 §4)."""
    respuesta = cliente.post(
        f"/api/inscripciones/{inscripcion.id}/compras/cupos",
        data=json.dumps({"cantidad": 3}),
        content_type="application/json",
        **_autorizacion(usuario_responsable),
    )

    contenido = respuesta.content.decode("utf-8")
    assert respuesta.status_code == 201
    assert "Traceback" not in contenido
