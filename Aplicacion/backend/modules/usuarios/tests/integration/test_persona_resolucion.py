"""
Resolver local → fuente externa: éxito, rechazo, fallo y recuperación.

GIVEN: una identidad se resuelve por documento.
WHEN: la persona existe localmente, o la fuente externa responde, o falla.
THEN: el origen es explícito, la fuente externa sólo se consulta si hace
falta, el fallo es RECUPERABLE y la persistencia sólo ocurre al confirmar.

Cubre `FR-03` §3 · `FL-02` · `RN-U03`.
"""

import pytest

from modules.usuarios.domain.constants import EstadoConsultaDocumentoChoices
from modules.usuarios.domain.models import Persona
from modules.usuarios.tests.fixtures.factories import (
    make_confirmar_payload,
    make_resolver_payload,
)
from modules.usuarios.tests.fixtures.persona_fixtures import (
    construir_resultado_externo,
    contar_personas,
    contar_personas_por_documento,
)


# ── Éxito ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_resolver_local_no_consulta_la_fuente_externa(
    auth_client,
    persona_creada,
    consulta_documento_client,
):
    """GIVEN una persona ya registrada · WHEN se resuelve · THEN la fuente
    externa NO se consulta (`FR-03` §3.2 regla 1)."""
    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(),
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["data"]["origen"] == "LOCAL"
    assert cuerpo["data"]["persona_id"] == str(persona_creada.id)
    assert cuerpo["data"]["persistida"] is True
    assert consulta_documento_client.llamadas == []


@pytest.mark.django_db(transaction=True)
async def test_resolver_externo_no_persiste(
    auth_client,
    consulta_documento_client,
):
    """GIVEN un documento que sólo existe en la fuente · WHEN se resuelve ·
    THEN devuelve los datos SIN persistir (`FR-03` §3.2 regla 2)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="87654321",
        nombre_completo="PEREZ, ANA",
    )

    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="87654321"),
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["origen"] == "EXTERNO"
    assert datos["persona_id"] is None
    assert datos["persistida"] is False
    assert datos["nombres"] == "ANA"
    assert datos["apellidos"] == "PEREZ"
    assert await contar_personas_por_documento("87654321") == 0
    assert consulta_documento_client.llamadas == ["87654321"]


@pytest.mark.django_db(transaction=True)
async def test_confirmar_persiste_la_identidad(
    auth_client,
    consulta_documento_client,
):
    """GIVEN una identidad resuelta · WHEN se confirma la operación · THEN la
    `Persona` queda persistida (`FR-03` §3.2 regla 2)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="87654321",
        nombre_completo="PEREZ, ANA",
    )
    await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="87654321"),
    )

    respuesta = await auth_client.post(
        "/personas/confirmar",
        json=make_confirmar_payload(numero_documento="87654321"),
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["numero_documento"] == "87654321"
    assert datos["origen_datos"] == "EXTERNO"
    assert datos["datos_obtenidos_en"] is not None
    assert await contar_personas_por_documento("87654321") == 1


# ── Rechazo ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_resolver_rechaza_tipo_documento_invalido(auth_client):
    """GIVEN un tipo de documento fuera del vocabulario · WHEN se resuelve ·
    THEN 422 `TIPO_DOCUMENTO_INVALIDO` (`FR-03` §1.1)."""
    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(tipo_documento="XXX"),
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "TIPO_DOCUMENTO_INVALIDO"


@pytest.mark.django_db(transaction=True)
async def test_confirmar_rechaza_documento_ya_vinculado_a_cuenta(
    auth_client,
    cuenta_con_persona,
):
    """GIVEN una identidad con cuenta · WHEN se confirma · THEN 409
    `PERSONA_DUPLICADA`: la identidad no se reescribe ni se duplica
    (`FR-03` §1.2)."""
    respuesta = await auth_client.post(
        "/personas/confirmar",
        json=make_confirmar_payload(),
    )

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "PERSONA_DUPLICADA"
    assert await contar_personas() == 1


# ── Fallo ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_resolver_falla_con_no_encontrado(
    auth_client,
    consulta_documento_client,
):
    """GIVEN un documento inexistente · WHEN se resuelve · THEN 404
    `PERSONA_NO_ENCONTRADA` (`FR-03` §3.1)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.NO_ENCONTRADO,
        numero_documento="99999999",
    )

    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="99999999"),
    )

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "PERSONA_NO_ENCONTRADA"


@pytest.mark.django_db(transaction=True)
async def test_resolver_falla_con_fuente_no_disponible(
    auth_client,
    consulta_documento_client,
):
    """GIVEN una fuente caída · WHEN se resuelve · THEN 503
    `FUENTE_EXTERNA_NO_DISPONIBLE` (`FR-03` §3.1)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE,
        numero_documento="99999999",
    )

    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="99999999"),
    )

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "FUENTE_EXTERNA_NO_DISPONIBLE"


@pytest.mark.django_db(transaction=True)
async def test_resolver_distingue_el_timeout(
    auth_client,
    consulta_documento_client,
):
    """GIVEN una fuente que agota el tiempo de espera · WHEN se resuelve ·
    THEN 504 `FUENTE_EXTERNA_TIMEOUT`: es un estado DISTINTO de la fuente
    caída (`FR-03` §3.3)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.TIMEOUT,
        numero_documento="99999999",
    )

    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="99999999"),
    )

    assert respuesta.status_code == 504
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "FUENTE_EXTERNA_TIMEOUT"


@pytest.mark.django_db(transaction=True)
async def test_resolver_distingue_los_datos_incompletos(
    auth_client,
    consulta_documento_client,
):
    """GIVEN una fuente que responde sin datos utilizables · WHEN se resuelve ·
    THEN 422 `PERSONA_DATOS_INCOMPLETOS`: no se fabrica ninguna identidad
    (`FR-03` §3.3, `contratos/03` §7)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS,
        numero_documento="99999999",
        nombre_completo="",
    )

    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="99999999"),
    )

    assert respuesta.status_code == 422, respuesta.json()
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "PERSONA_DATOS_INCOMPLETOS", cuerpo
    assert await contar_personas_por_documento("99999999") == 0, cuerpo


@pytest.mark.django_db(transaction=True)
async def test_resolver_exige_sesion(api_client, consulta_documento_client):
    """GIVEN un cliente anónimo · WHEN se resuelve · THEN 401: la
    autenticación se resuelve ANTES que la autorización."""
    respuesta = await api_client.post(
        "/personas/resolver",
        json=make_resolver_payload(),
    )

    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ── Recuperación ────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_el_fallo_de_la_fuente_es_recuperable(
    auth_client,
    consulta_documento_client,
):
    """GIVEN una fuente caída · WHEN se reintenta con la fuente recuperada ·
    THEN la segunda vez resuelve (`FR-03` §3.3 — el fallo es reintentable)."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE,
        numero_documento="87654321",
    )
    primera = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="87654321"),
    )
    assert primera.status_code == 503

    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="87654321",
    )
    segunda = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="87654321"),
    )

    assert segunda.status_code == 200
    assert segunda.json()["data"]["origen"] == "EXTERNO"


@pytest.mark.django_db(transaction=True)
async def test_consulta_externa_es_publica(api_client, consulta_documento_client):
    """GIVEN un cliente anónimo · WHEN se consulta el documento externo ·
    THEN responde 200: es el autocompletado, no una superficie de sesión."""
    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="87654321",
    )

    respuesta = await api_client.get("/personas/busqueda/87654321")

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["tipo_documento"] == "DNI"
    assert datos["nombre_completo"] == "PEREZ, ANA"
