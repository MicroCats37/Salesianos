"""
Creación concurrente de una identidad por documento.

GIVEN: dos peticiones que confirman el MISMO documento.
WHEN: la segunda llega después de que la primera ya escribió.
THEN: no hay duplicado, no hay `IntegrityError` sin controlar y las dos
terminan en la MISMA persona (`RN-U03` · `FR-03` §3.2 regla 3).

La autoridad es la `UniqueConstraint` de la base de datos; el código NO usa
`get_or_create` silencioso, que ocultaría la carrera.
"""

import pytest
from django.db import IntegrityError

from modules.usuarios.domain.models import Persona
from modules.usuarios.tests.fixtures.factories import make_confirmar_payload
from modules.usuarios.tests.fixtures.persona_fixtures import (
    contar_personas_por_documento,
)

#: Documento de la identidad que compite (registrada, pero SIN cuenta).
DOCUMENTO_COMPETIDOR = "44555666"


@pytest.mark.django_db(transaction=True)
def test_la_base_de_datos_rechaza_el_documento_duplicado(
    persona_registrada_sin_cuenta,
):
    """GIVEN una persona registrada · WHEN se inserta el mismo documento ·
    THEN la base de datos lo rechaza (`FR-03` §1.1)."""
    with pytest.raises(IntegrityError):
        Persona.objects.create(
            tipo_documento="DNI",
            numero_documento=persona_registrada_sin_cuenta.numero_documento,
            nombres="OTRA",
            apellidos="PERSONA",
        )


@pytest.mark.django_db(transaction=True)
async def test_la_carrera_perdida_reutiliza_la_fila_ganadora(
    auth_client,
    persona_registrada_sin_cuenta,
):
    """GIVEN que otra petición YA registró el documento · WHEN esta petición
    confirma la misma identidad · THEN devuelve ESA persona y no crea otra.

    Es exactamente el camino que recorre la petición que pierde la carrera:
    el `IntegrityError` de la base de datos se reintenta de forma controlada
    y la fila ganadora se reutiliza.
    """
    respuesta = await auth_client.post(
        "/personas/confirmar",
        json=make_confirmar_payload(numero_documento=DOCUMENTO_COMPETIDOR),
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["id"] == str(persona_registrada_sin_cuenta.id)
    assert await contar_personas_por_documento(DOCUMENTO_COMPETIDOR) == 1


@pytest.mark.django_db(transaction=True)
async def test_confirmar_dos_veces_no_duplica(
    auth_client,
    persona_registrada_sin_cuenta,
):
    """GIVEN una identidad · WHEN se confirma dos veces · THEN sigue habiendo
    una sola persona con ese documento."""
    primera = await auth_client.post(
        "/personas/confirmar",
        json=make_confirmar_payload(numero_documento=DOCUMENTO_COMPETIDOR),
    )
    segunda = await auth_client.post(
        "/personas/confirmar",
        json=make_confirmar_payload(numero_documento=DOCUMENTO_COMPETIDOR),
    )

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert primera.json()["data"]["id"] == segunda.json()["data"]["id"]
    assert await contar_personas_por_documento(DOCUMENTO_COMPETIDOR) == 1


@pytest.mark.django_db(transaction=True)
async def test_confirmaciones_simultaneas_no_duplican(
    auth_client,
    persona_registrada_sin_cuenta,
):
    """GIVEN dos peticiones simultáneas con el mismo documento · WHEN ambas
    confirman · THEN queda UNA sola persona (`RN-U03`)."""
    import asyncio

    respuestas = await asyncio.gather(
        auth_client.post(
            "/personas/confirmar",
            json=make_confirmar_payload(numero_documento=DOCUMENTO_COMPETIDOR),
        ),
        auth_client.post(
            "/personas/confirmar",
            json=make_confirmar_payload(numero_documento=DOCUMENTO_COMPETIDOR),
        ),
        return_exceptions=True,
    )

    codigos = [
        getattr(respuesta, "status_code", None) for respuesta in respuestas
    ]
    assert all(codigo == 200 for codigo in codigos), codigos
    assert await contar_personas_por_documento(DOCUMENTO_COMPETIDOR) == 1
