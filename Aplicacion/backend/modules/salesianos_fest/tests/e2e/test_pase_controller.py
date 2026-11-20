"""Superficie HTTP de los pases, los beneficiarios y las cortesías.

GIVEN  un pase vigente, una compra y una cuenta de administrador
WHEN   se consulta el catálogo, se compra, se asigna un beneficiario, se
       revoca y se otorga una cortesía
THEN   responde el envelope congelado con los códigos de error estables del
       ledger (`RT-PS-01`…`RT-PS-08`, `RT-CM-02`, `RT-RT-03`).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).

**NO EJECUTADO.** La verificación en runtime de este paquete está DIFERIDA
por instrucción explícita del usuario. Ver
`evidence/domains/DOM-03-pases-beneficios-cortesia.md` §6.
"""

import json

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


def _con_token(token: str) -> dict:
    """El header del token privado de gestión."""
    return {"HTTP_X_PASE_TOKEN": token}


# ── RT-PS-01 / RT-PS-02 · El catálogo ───────────────────────────────────────


def test_el_catalogo_publica_el_prefe_vigente(cliente, pase, edicion_con_pases):
    """GIVEN un pase vigente con precio
    WHEN  se consulta el catálogo
    THEN  responde 200 con el pase y su precio: el catálogo es de UNA
       edición (`RN-E01`).
    """
    respuesta = cliente.get(f"/api/pases?edicion_id={edicion_con_pases.id}")

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert len(cuerpo["data"]["pases"]) == 1
    assert cuerpo["data"]["pases"][0]["nombre"] == "Pase FEST"
    assert float(cuerpo["data"]["pases"][0]["precio"]["monto"]) == 35.0


def test_un_pase_sin_precio_no_aparece(cliente, pase_sin_precio, edicion_con_pases):
    """GIVEN un pase VIGENTE sin precio vigente
    WHEN  se consulta el catálogo
    THEN  NO aparece: no hay precio de reserva (`FL-01` paso 3).
    """
    respuesta = cliente.get(f"/api/pases?edicion_id={edicion_con_pases.id}")

    assert respuesta.status_code == 200
    assert json.loads(respuesta.content)["data"]["pases"] == []


def test_una_edicion_sin_el_modulo_no_expone_catalogo(
    cliente, edicion_sin_modulo
):
    """GIVEN una edición sin el módulo `pases` habilitado
    WHEN  se consulta el catálogo
    THEN  responde con el error de módulo no habilitado, no un catálogo
       vacío (`RN-E02`).
    """
    respuesta = cliente.get(f"/api/pases?edicion_id={edicion_sin_modulo.id}")

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "MODULO_NO_HABILITADO"


# ── RT-CM-02 · La compra ────────────────────────────────────────────────────


def test_comprar_pases_sin_cuenta_responde_201(cliente, pase):
    """GIVEN un visitante SIN cuenta
    WHEN  compra dos pases
    THEN  responde 201 con la compra PENDIENTE, el importe congelado y el
       token de gestión (`RT-CM-02`, `RN-C02`, `RN-P02`).
    """
    respuesta = cliente.post(
        "/api/pases/compras",
        data=json.dumps(
            {
                "pase_id": str(pase.id),
                "cantidad": 2,
                "tipo_documento": "DNI",
                "numero_documento": "90909090",
                "nombres": "Visitante",
                "apellidos": "Invitado",
                "contacto_email": "visitante@example.com",
            }
        ),
        content_type="application/json",
    )

    assert respuesta.status_code == 201
    cuerpo = json.loads(respuesta.content)
    datos = cuerpo["data"]
    assert datos["estado"] == "PENDIENTE"
    assert datos["cantidad"] == 2
    assert float(datos["total"]) == 70.0
    assert datos["token"]
    assert datos["causa_operativa"] == "COMPRA_PASE_CREADA"


def test_comprar_una_cantidad_invalida_es_422(cliente, pase):
    """GIVEN una cantidad fuera de los límites
    WHEN  se intenta comprar
    THEN  responde 422 con el código CONGELADO `CANTIDAD_INVALIDA`.
    """
    respuesta = cliente.post(
        "/api/pases/compras",
        data=json.dumps(
            {
                "pase_id": str(pase.id),
            "cantidad": 51,
                "tipo_documento": "DNI",
                "numero_documento": "90909091",
                "nombres": "Visitante",
            }
        ),
        content_type="application/json",
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "CANTIDAD_INVALIDA"


def test_comprar_un_pase_inexistente_es_409(cliente, edicion_con_pases):
    """GIVEN un pase que no existe
    WHEN  se intenta comprar
    THEN  responde 409 con el código CONGELADO `PASE_NO_DISPONIBLE`.
    """
    from uuid import uuid4

    respuesta = cliente.post(
        "/api/pases/compras",
        data=json.dumps(
            {
                "pase_id": str(uuid4()),
                "cantidad": 1,
                "tipo_documento": "DNI",
                "numero_documento": "90909092",
                "nombres": "Visitante",
            }
        ),
        content_type="application/json",
    )

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "PASE_NO_DISPONIBLE"


# ── RT-PS-03 / RT-PS-04 · La gestión del lote ───────────────────────────────


def test_sin_credencial_el_lote_no_se_abre(cliente, compra_pase_pagada):
    """GIVEN una petición SIN cuenta y SIN token
    WHEN  se consulta el lote
    THEN  responde 401 con `TOKEN_PASE_INVALIDO`: la autenticación va antes
       que la autorización, y el DNI NO es una credencial.
    """
    respuesta = cliente.get(f"/api/pases/compras/{compra_pase_pagada.id}")

    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "TOKEN_PASE_INVALIDO"


def test_el_token_del_enlace_abre_el_lote(cliente, compra_pase_pagada):
    """GIVEN el token del enlace
    WHEN  se consulta el lote con la cabecera `X-Pase-Token`
    THEN  responde 200 con el detalle y sus beneficiarios.
    """
    respuesta = cliente.get(
        f"/api/pases/compras/{compra_pase_pagada.id}",
        **_con_token(compra_pase_pagada.token),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["data"]["compra_pase_id"] == str(compra_pase_pagada.id)
    assert cuerpo["data"]["cantidad"] == 2


def test_una_cuenta_ajena_no_abre_el_lote(
    cliente, compra_pase_pagada, usuario_ajeno
):
    """GIVEN una cuenta que NO es la compradora
    WHEN  se consulta el lote
    THEN  responde 403 con `COMPRA_PASE_NO_AUTORIZADA`.
    """
    respuesta = cliente.get(
        f"/api/pases/compras/{compra_pase_pagada.id}",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "COMPRA_PASE_NO_AUTORIZADA"


# ── RT-PS-05 · La asignación ─────────────────────────────────────────────────


def test_asignar_un_beneficiario_actualiza_el_lote(
    cliente, compra_pase_pagada, persona_participante
):
    """GIVEN un lote pagado
    WHEN  se asigna un beneficiario con el token del enlace
    THEN  responde 200 con la aritmética del servidor (`RN-P07`).
    """
    respuesta = cliente.post(
        f"/api/pases/compras/{compra_pase_pagada.id}/beneficiarios",
        data=json.dumps({"persona_id": str(persona_participante.id)}),
        content_type="application/json",
        **_con_token(compra_pase_pagada.token),
    )

    assert respuesta.status_code == 200
    datos = json.loads(respuesta.content)["data"]
    assert datos["asignados"] == 1
    assert datos["disponibles"] == 1
    assert datos["beneficiarios"][0]["origen"] == "COMPRA"


def test_asignar_un_duplicado_es_409(
    cliente, compra_pase_pagada, persona_participante
):
    """GIVEN una persona que YA tiene un derecho activo
    WHEN  se intenta asignarle otro pase del mismo lote
    THEN  responde 409 con `PASE_DUPLICADO`.
    """
    payload = json.dumps({"persona_id": str(persona_participante.id)})
    cabeceras = _con_token(compra_pase_pagada.token)
    cliente.post(
        f"/api/pases/compras/{compra_pase_pagada.id}/beneficiarios",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )

    respuesta = cliente.post(
        f"/api/pases/compras/{compra_pase_pagada.id}/beneficiarios",
        data=payload,
        content_type="application/json",
        **cabeceras,
    )

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "PASE_DUPLICADO"


def test_asignar_a_un_lote_pendiente_es_409(
    cliente, compra_pase_pendiente, persona_participante
):
    """GIVEN un lote PENDIENTE
    WHEN  se intenta asignar un beneficiario
    THEN  responde 409 con `COMPRA_PASE_NO_PAGADA` (`RN-P02`).
    """
    respuesta = cliente.post(
        f"/api/pases/compras/{compra_pase_pendiente.id}/beneficiarios",
        data=json.dumps({"persona_id": str(persona_participante.id)}),
        content_type="application/json",
        **_con_token(compra_pase_pendiente.token),
    )

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "COMPRA_PASE_NO_PAGADA"


# ── RT-RT-03 · La revocación ────────────────────────────────────────────────


def test_revocar_un_beneficiario_es_idempotente(
    cliente, compra_pase_pagada, beneficiario_pase
):
    """GIVEN un derecho activo
    WHEN  se revoca dos veces
    THEN  responde 200 las dos veces: la revocación es idempotente
       (`FR-05` §2.3).
    """
    url = (
        f"/api/pases/compras/{compra_pase_pagada.id}"
        f"/beneficiarios/{beneficiario_pase.persona_id}"
    )
    cabeceras = _con_token(compra_pase_pagada.token)

    primera = cliente.delete(url, **cabeceras)
    segunda = cliente.delete(url, **cabeceras)

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert json.loads(primera.content)["data"]["ya_revocado"] is False
    assert json.loads(segunda.content)["data"]["ya_revocado"] is True


# ── RT-PS-08 · La cortesía ───────────────────────────────────────────────────


def test_otorgar_una_cortesia_registra_el_acta(
    cliente, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN un administrador
    WHEN  otorga una cortesía
    THEN  responde 201 con el acta, su actor y su motivo (`RT-PS-08`).
    """
    respuesta = cliente.post(
        "/api/administracion/pases/cortesias",
        data=json.dumps(
            {
                "edicion_id": str(edicion_con_pases.id),
                "pase_id": str(pase.id),
                "persona_id": str(persona_ajena.id),
                "motivo": "Invitación del inteligible.",
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 201
    datos = json.loads(respuesta.content)["data"]
    assert datos["motivo"] == "Invitación del inteligible."
    assert datos["actor_usuario_id"] == str(usuario_admin.id)
    assert datos["estado"] == "ACTIVA"


def test_otorgar_una_cortesia_sin_cuenta_es_401(
    cliente, pase, edicion_con_pases, persona_ajena
):
    """GIVEN una petición SIN cuenta
    WHEN  se intenta otorgar una cortesía
    THEN  responde 401: una cortesía siempre tiene actor (`RN-P05`).
    """
    respuesta = cliente.post(
        "/api/administracion/pases/cortesias",
        data=json.dumps(
            {
                "edicion_id": str(edicion_con_pases.id),
                "pase_id": str(pase.id),
                "persona_id": str(persona_ajena.id),
                "motivo": "Invitación del inteligible.",
            }
        ),
        content_type="application/json",
    )

    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_otorgar_una_cortesia_sin_motivo_es_422(
    cliente, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN una cortesía SIN motivo
    WHEN  se intenta otorgar
    THEN  responde 422 con `CORTESIA_MOTIVO_INVALIDO` (`RN-P05`).
    """
    respuesta = cliente.post(
        "/api/administracion/pases/cortesias",
        data=json.dumps(
            {
                "edicion_id": str(edicion_con_pases.id),
                "pase_id": str(pase.id),
                "persona_id": str(persona_ajena.id),
                "motivo": "",
            }
        ),
        content_type="application/json",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 422
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "CORTESIA_MOTIVO_INVALIDO"


# ── RT-PS-06 / RT-PS-07 · La administración ──────────────────────────────────


def test_el_listado_de_lotes_no_expone_el_token(
    cliente, compra_pase_pagada, usuario_admin
):
    """GIVEN un lote comprado
    WHEN  un administrador lista los lotes
    THEN  responde 200 y el token NO aparece: es una credencial.
    """
    respuesta = cliente.get(
        "/api/administracion/pases",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode("utf-8")
    assert compra_pase_pagada.token not in contenido
    assert json.loads(respuesta.content)["data"]["total"] == 1


def test_el_listado_exige_cuenta_de_administrador(cliente, usuario_ajeno):
    """GIVEN una cuenta que NO es administradora
    WHEN  se lista el inventario
    THEN  responde 403 con `ACTION_NOT_ALLOWED`.
    """
    respuesta = cliente.get(
        "/api/administracion/pases",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "ACTION_NOT_ALLOWED"


# ── La seguridad del envelope ───────────────────────────────────────────────


def test_la_respuesta_no_expone_identificadores_internos(cliente, pase):
    """El envelope público no filtra trazas ni texto crudo (FR-01 §4)."""
    respuesta = cliente.post(
        "/api/pases/compras",
        data=json.dumps(
            {
                "pase_id": str(pase.id),
                "cantidad": 1,
                "tipo_documento": "DNI",
                "numero_documento": "90909099",
                "nombres": "Visitante",
            }
        ),
        content_type="application/json",
    )

    contenido = respuesta.content.decode("utf-8")
    assert respuesta.status_code == 201
    assert "Traceback" not in contenido
    assert "sqlite" not in contenido.lower()
