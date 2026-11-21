"""El CAMINO ADMINISTRATIVO COMPLETO de la credencial de puerta.

GIVEN  un administrador
WHEN   otorga una cortesía, lista las cortesías y emite la credencial del
       `derecho_id` que el LISTADO publica
THEN   la credencial se emite contra ESE derecho, su código es el que
       funciona en la puerta y la emisión es ONE-SHOT (`FR-05` §1).

**ÉSTE es el hueco que el correctivo cierra.** Antes, el listado NO
publicaba el `derecho_id`: la emisión de credenciales existía pero era
INACCESIBLE desde ADM-15.

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).

Change: `administracion-pases-alta-directa` · Apply C (correctivo)
"""

import json

import pytest
from ninja_jwt.tokens import AccessToken

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("modules.salesianos_fest.tests.urls_cortesia_credencial"),
]

#: La ruta del listado administrativo de cortesías.
RUTA_CORTESIAS = "/api/administracion/pases/cortesias"

#: La ruta de la emisión de la credencial de puerta.
RUTA_TICKETS = "/api/validaciones/tickets"

#: La ruta de la comprobación de una credencial en la puerta.
RUTA_PREVIEW = "/api/validaciones/preview"


@pytest.fixture
def cabeceras(db, usuario_admin):
    """La cabecera de autorización del administrador."""
    token = AccessToken.for_user(usuario_admin)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _otorgar(client, cabeceras, edicion_id, pase_id, persona):
    """La petición de otorgamiento de una cortesía."""
    return client.post(
        RUTA_CORTESIAS,
        data=json.dumps(
            {
                "edicion_id": str(edicion_id),
                "pase_id": str(pase_id),
                "tipo_documento": persona.tipo_documento,
                "numero_documento": persona.numero_documento,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "motivo": "Invitación del inteligible.",
            }
        ),
        content_type="application/json",
        **cabeceras,
    )


def _listar(client, cabeceras, edicion_id):
    """La petición del listado administrativo de cortesías."""
    return client.get(
        f"{RUTA_CORTESIAS}?edicion_id={edicion_id}",
        **cabeceras,
    )


def _emitir(client, cabeceras, derecho_id):
    """La petición de emisión de la credencial de un derecho."""
    return client.post(
        RUTA_TICKETS,
        data=json.dumps({"derecho_id": str(derecho_id)}),
        content_type="application/json",
        **cabeceras,
    )


# ── El `derecho_id` publicado ───────────────────────────────────────────────


def test_el_listado_publica_el_derecho_por_http(
    client, cabeceras, cortesia_pase, edicion_con_pases
):
    """GIVEN una cortesía con su derecho
    WHEN  se lista por HTTP
    THEN  la fila publica el identificador EXACTO del `PaseBeneficiario`.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)

    respuesta = _listar(client, cabeceras, edicion_con_pases.id)

    assert respuesta.status_code == 200
    filas = respuesta.json()["data"]["items"]
    assert len(filas) == 1
    assert filas[0]["derecho_id"] == str(derecho.id)


def test_el_otorgamiento_publica_el_derecho_por_http(
    client, cabeceras, pase, edicion_con_pases, persona_ajena
):
    """GIVEN una cortesía otorgada por HTTP
    WHEN  se lee la respuesta
    THEN  publica el identificador del DERECHO que se creó con ella.
    """
    respuesta = _otorgar(client, cabeceras, edicion_con_pases.id, pase.id, persona_ajena)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["message"] == "Cortesía registrada correctamente."

    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(persona=persona_ajena)
    assert cuerpo["data"]["derecho_id"] == str(derecho.id)


def test_un_acta_sin_derecho_publica_ausente_por_http(
    client, cabeceras, pase, edicion_con_pases, persona_ajena, usuario_admin
):
    """GIVEN un acta SIN derecho (corrupción histórica)
    WHEN  se lista por HTTP
    THEN  la fila publica `derecho_id = None`: el identificador ausente nunca
       se inventa.
    """
    from modules.salesianos_fest.domain.models import CortesiaPase

    CortesiaPase.objects.create(
        edicion=edicion_con_pases,
        pase=pase,
        persona=persona_ajena,
        actor_usuario=usuario_admin,
        actor_persona=usuario_admin.persona_fk,
        motivo="Acta sin derecho (corrupción histórica).",
        estado="ACTIVA",
    )

    respuesta = _listar(client, cabeceras, edicion_con_pases.id)

    filas = respuesta.json()["data"]["items"]
    assert len(filas) == 1
    assert filas[0]["derecho_id"] is None


# ── La credencial reachable desde el listado ────────────────────────────────


def test_la_credencial_se_emite_contra_el_derecho_publicado(
    client, cabeceras, cortesia_pase, edicion_con_pases
):
    """GIVEN el `derecho_id` que publica el listado
    WHEN  se emite la credencial
    THEN  responde 201 con un código de puerta y el tipo DERIVADO
       (`ENTRADA_CORTESIA`): el navegador no declara el tipo (`RN-U04`).
    """
    listado = _listar(client, cabeceras, edicion_con_pases.id)
    derecho_id = listado.json()["data"]["items"][0]["derecho_id"]

    respuesta = _emitir(client, cabeceras, derecho_id)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["message"] == "Credencial emitida correctamente."

    datos = cuerpo["data"]
    assert datos["codigo"].startswith("FEST-")
    assert datos["tipo_derecho"] == "ENTRADA_CORTESIA"
    assert datos["operacion"] == "INGRESO"
    assert datos["edicion_id"] == str(edicion_con_pases.id)


def test_la_credencial_publicada_es_la_que_funciona_en_la_puerta(
    client, cabeceras, cortesia_pase, edicion_con_pases
):
    """GIVEN una credencial emitida
    WHEN  se comprueba en la puerta
    THEN  la puerta la reconoce y publica a su titular: el código entregado
       es el código que sirve.
    """
    listado = _listar(client, cabeceras, edicion_con_pases.id)
    derecho_id = listado.json()["data"]["items"][0]["derecho_id"]

    credencial = _emitir(client, cabeceras, derecho_id).json()["data"]

    comprobacion = client.post(
        RUTA_PREVIEW,
        data=json.dumps({"codigo": credencial["codigo"]}),
        content_type="application/json",
        **cabeceras,
    )

    assert comprobacion.status_code == 200
    cuerpo = comprobacion.json()
    assert cuerpo["success"] is True
    assert cortesia_pase.persona.nombres in cuerpo["data"]["titular"]["nombre"]
    assert cuerpo["data"]["puede_canjear"] is True


def test_la_emision_es_one_shot(
    client, cabeceras, cortesia_pase, edicion_con_pases
):
    """GIVEN un derecho que YA tiene credencial
    WHEN  se emite OTRA para el mismo derecho
    THEN  se rechaza con 409 `CONFLICT`: dos códigos vivos duplicarían el
       acceso (`FR-05` §1).
    """
    from modules.validaciones.domain.models import Ticket

    listado = _listar(client, cabeceras, edicion_con_pases.id)
    derecho_id = listado.json()["data"]["items"][0]["derecho_id"]

    primera = _emitir(client, cabeceras, derecho_id)
    assert primera.status_code == 201

    segunda = _emitir(client, cabeceras, derecho_id)
    assert segunda.status_code == 409
    assert segunda.json()["error"]["code"] == "CONFLICT"
    assert Ticket.objects.count() == 1


# ── Los errores ─────────────────────────────────────────────────────────────


def test_sin_sesion_no_se_publica_el_derecho(
    client, cortesia_pase, edicion_con_pases
):
    """GIVEN una petición sin cuenta
    WHEN  se lista
    THEN  responde 401: el listado de cortesías es administrativo.
    """
    respuesta = client.get(f"{RUTA_CORTESIAS}?edicion_id={edicion_con_pases.id}")

    assert respuesta.status_code == 401


def test_sin_autorizacion_no_se_emite_la_credencial(
    client, db, usuario_responsable, cortesia_pase, edicion_con_pases
):
    """GIVEN una cuenta sin la capacidad de acreditaciones
    WHEN  se emite la credencial
    THEN  responde 403.
    """
    from modules.salesianos_fest.domain.models import PaseBeneficiario

    derecho = PaseBeneficiario.objects.get(cortesia=cortesia_pase)
    token = AccessToken.for_user(usuario_responsable)

    respuesta = _emitir(
        client,
        {"HTTP_AUTHORIZATION": f"Bearer {token}"},
        derecho.id,
    )

    assert respuesta.status_code == 403
