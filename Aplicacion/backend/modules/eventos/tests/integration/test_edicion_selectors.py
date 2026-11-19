"""`EdicionSelector`: superficie de lectura y aislamiento entre ediciones.

GIVEN  un catálogo con ediciones de varias ediciones y eventos
WHEN   se consulta el selector
THEN   cada lectura devuelve lo que pertenece a SU edición y nada más.
"""

import uuid

import pytest

from modules.eventos.domain.models import Edicion


@pytest.mark.django_db
def test_obtener_por_id_devuelve_la_edicion(edicion_selector, edicion_borrador):
    assert edicion_selector.obtener_por_id(str(edicion_borrador.id)) == edicion_borrador


@pytest.mark.django_db
def test_obtener_por_id_acepta_un_uuid(edicion_selector, edicion_borrador):
    assert edicion_selector.obtener_por_id(edicion_borrador.id) == edicion_borrador


@pytest.mark.django_db
def test_obtener_por_id_desconocido_devuelve_none(edicion_selector, db):
    assert edicion_selector.obtener_por_id(uuid.uuid4()) is None


@pytest.mark.django_db
def test_obtener_por_id_mal_formado_devuelve_none(edicion_selector, db):
    """Un identificador mal formado NO es un 500: es "no existe"."""
    assert edicion_selector.obtener_por_id("no-soy-una-edicion") is None
    assert edicion_selector.obtener_por_id("") is None
    assert edicion_selector.obtener_por_id(None) is None


@pytest.mark.django_db
def test_obtener_por_slug_es_unico_por_evento(
    edicion_selector, evento, evento_otro
):
    """El slug de una edición sólo resuelve dentro de SU evento."""
    primera = Edicion.objects.create(evento=evento, nombre="A", slug="2026", anio=2026)
    segunda = Edicion.objects.create(
        evento=evento_otro,
        nombre="B",
        slug="2026",
        anio=2026,
    )

    assert edicion_selector.obtener_por_slug(evento.id, "2026") == primera
    assert edicion_selector.obtener_por_slug(evento_otro.id, "2026") == segunda
    assert edicion_selector.obtener_por_slug(evento.id, "2027") is None


@pytest.mark.django_db
def test_listar_por_evento_no_filtra_entre_ediciones(
    edicion_selector, evento, evento_otro, edicion_borrador
):
    """AISLAMIENTO: el listado de un evento no incluye las ediciones de otro."""
    ajena = Edicion.objects.create(
        evento=evento_otro,
        nombre="Ajena",
        slug="ajena",
        anio=2025,
    )

    listado = list(edicion_selector.listar_por_evento(evento.id))

    assert edicion_borrador in listado
    assert ajena not in listado


@pytest.mark.django_db
def test_contar_publicadas_solo_cuenta_las_publicadas(
    edicion_selector, edicion_borrador, edicion_cerrada, edicion_publicada
):
    assert edicion_selector.contar_publicadas() == 1


@pytest.mark.django_db
def test_contar_publicadas_cero_sin_publicadas(
    edicion_selector, edicion_borrador, edicion_cerrada
):
    assert edicion_selector.contar_publicadas() == 0
    assert edicion_selector.contar() == 2


@pytest.mark.django_db
def test_obtener_publicada_devuelve_none_si_hay_mas_de_una(
    edicion_selector, edicion_publicada, evento_otro
):
    """Con más de una publicada NO se elige una: el selector no decide."""
    Edicion.objects.create(
        evento=evento_otro,
        nombre="Otra",
        slug="otra",
        anio=2027,
        estado="PUBLICADA",
    )

    assert edicion_selector.obtener_publicada() is None
    assert edicion_selector.contar_publicadas() == 2


@pytest.mark.django_db
def test_listar_publicadas_es_estable(edicion_selector, edicion_publicada):
    assert list(edicion_selector.listar_publicadas()) == [edicion_publicada]


@pytest.mark.django_db
def test_listar_devuelve_todas_las_ediciones(edicion_selector, edicion_borrador, edicion_cerrada):
    listado = list(edicion_selector.listar())

    assert edicion_borrador in listado
    assert edicion_cerrada in listado
