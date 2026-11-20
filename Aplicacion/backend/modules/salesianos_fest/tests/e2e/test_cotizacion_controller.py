"""`POST /cotizaciones` en el API PERMANENTE de la aplicación.

Change: `salesianos-fest-rebuild` · Corrective apply (2026-11-20) ·
Owner: DOM-01 (A3) para el presenter, A0 para el registro.

`evidence/verification/VER-01-baseline-regression-payments.md` probó DOS
defectos distintos en esta misma ruta:

- §6.1 (B-F1): `POST /cotizaciones` respondía **HTTP 500**. El presenter leía
  `result.paqueta_id` y el resultado expone `paquete_id`: un `AttributeError`
  en `catalogo_presenter.py`.
- §7.1 (DRIFT A · `A0-API02-09`): la ruta **NO EXISTÍA**, porque
  `CotizacionController` estaba implementado y NO registrado en
  `config/api.py`. El frontend la consume HOY.

Este módulo prueba las DOS cosas a la vez, y lo hace sobre el **URLconf real
de la aplicación** (`config.urls`), no sobre un URLconf de pruebas: si el
controller no estuviera registrado en `config/api.py`, el cliente respondería
**404** y la prueba caería.

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json
from decimal import Decimal

import pytest
from django.test import Client

pytestmark = [
    pytest.mark.urls("config.urls"),
    pytest.mark.django_db,
]


@pytest.fixture
def cliente():
    """Cliente HTTP de prueba."""
    return Client()


def test_la_ruta_de_cotizacion_esta_registrada_en_el_api_permanente():
    """GIVEN el API permanente (`config/api.py`)
    WHEN  se lee su superficie OpenAPI
    THEN  la ruta `POST /api/cotizaciones` EXISTE: deja de ser código muerto.
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert "/api/cotizaciones" in paths
    assert "post" in paths["/api/cotizaciones"]


def test_la_cotizacion_responde_200_y_trae_el_identificador_del_paquete(
    cliente, edicion_publicada, paquete, disciplina, precio
):
    """GIVEN un paquete vigente con precio
    WHEN  se cotiza para 12 participantes
    THEN  responde 200 y la respuesta trae `paquete_id`: el campo que el
       presenter leía mal (`paqueta_id`) y que provocaba el HTTP 500.
    """
    respuesta = cliente.post(
        "/api/cotizaciones",
        data=json.dumps({"paquete_id": str(paquete.id), "cantidad": 12}),
        content_type="application/json",
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)["data"]
    assert cuerpo["paquete_id"] == str(paquete.id)
    assert cuerpo["paquete_nombre"] == paquete.nombre
    assert cuerpo["minimo_cantidad"] == 10
    assert cuerpo["cantidad_cotizada"] == 12
    assert Decimal(str(cuerpo["precio_unitario"])) == Decimal("250.00")
    assert Decimal(str(cuerpo["total"])) == Decimal("3000.00")


def test_la_cotizacion_no_devuelve_500_ni_traza(
    cliente, edicion_publicada, paquete, disciplina, precio
):
    """La ruta viva NO devuelve 500 ni filtra la traza (FR-01 §4)."""
    respuesta = cliente.post(
        "/api/cotizaciones",
        data=json.dumps({"paquete_id": str(paquete.id), "cantidad": 12}),
        content_type="application/json",
    )

    contenido = respuesta.content.decode("utf-8")
    assert respuesta.status_code == 200
    assert "Traceback" not in contenido
    assert "paqueta_id" not in contenido
