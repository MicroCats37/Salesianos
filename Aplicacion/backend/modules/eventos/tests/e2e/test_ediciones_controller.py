"""Superficie HTTP de las ediciones: `GET /api/ediciones/actual`.

GIVEN  un catálogo con la edición publicada, sin edición publicada o con dos
WHEN   se consulta la ruta
THEN   responde el envelope congelado con la edición y sus módulos, o el error
       estable del catálogo — nunca una edición elegida por defecto.

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1): maneja las corrutinas
internamente y corre en el hilo del test, de modo que la conexión de base de
datos es la del test.
"""

import json

import pytest
from django.test import Client

from modules.eventos.domain.models import Edicion

pytestmark = pytest.mark.urls("modules.eventos.tests.urls_eventos")


@pytest.fixture
def cliente():
    """Cliente HTTP sin autenticación (la ruta es pública)."""
    return Client()


@pytest.mark.django_db
def test_devuelve_la_edicion_publicada_y_sus_modulos(cliente, edicion_publicada):
    edicion_publicada.modulos_habilitados = ["inscripciones"]
    edicion_publicada.save()

    respuesta = cliente.get("/api/ediciones/actual")

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["id"] == str(edicion_publicada.id)
    assert cuerpo["data"]["nombre"] == "Salesianos FEST 2027"
    assert cuerpo["data"]["estado"] == "PUBLICADA"
    assert cuerpo["data"]["evento_slug"] == "salesianos-fest"

    modulos = {modulo["clave"]: modulo["habilitado"] for modulo in cuerpo["data"]["modulos"]}
    assert modulos == {
        "inscripciones": True,
        "pases": False,
        "marketplace": False,
        "competencias": False,
        "patrocinadores": False,
    }


@pytest.mark.django_db
def test_no_publicada_responde_404_con_codigo_estable(
    cliente, edicion_borrador, edicion_cerrada
):
    """Hay ediciones pero ninguna publicada: 404 EDICION_NO_PUBLICADA."""
    respuesta = cliente.get("/api/ediciones/actual")

    assert respuesta.status_code == 404
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "EDICION_NO_PUBLICADA"


@pytest.mark.django_db
def test_sin_ediciones_responde_404_no_resuelta(cliente, db):
    """No hay nada que resolver: 404 EDICION_NO_RESUELTA."""
    respuesta = cliente.get("/api/ediciones/actual")

    assert respuesta.status_code == 404
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "EDICION_NO_RESUELTA"


@pytest.mark.django_db
def test_dos_publicadas_responde_409_ambigua(cliente, edicion_publicada, evento_otro):
    """Dos ediciones publicadas: 409 EDICION_AMBIGUA, nunca una elegida."""
    Edicion.objects.create(
        evento=evento_otro,
        nombre="Otra",
        slug="otra",
        anio=2027,
        estado="PUBLICADA",
    )

    respuesta = cliente.get("/api/ediciones/actual")

    assert respuesta.status_code == 409
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "EDICION_AMBIGUA"


@pytest.mark.django_db
def test_la_respuesta_no_expone_identificadores_internos(cliente, edicion_publicada):
    """El envelope público no filtra texto crudo ni trazas (FR-01 §4)."""
    respuesta = cliente.get("/api/ediciones/actual")

    cuerpo = json.loads(respuesta.content)
    assert respuesta.status_code == 200
    assert cuerpo["message"] is None
    assert "Traceback" not in respuesta.content.decode("utf-8")
