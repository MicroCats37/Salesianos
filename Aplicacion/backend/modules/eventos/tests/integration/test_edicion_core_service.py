"""Escrituras sobre ediciones: alta, publicación, cierre y habilitación.

GIVEN  una edición con su alcance resuelto
WHEN   se escribe sobre ella
THEN   la escritura es explícita, la invariante de una única edición publicada
       por evento la hace cumplir la base de datos y el módulo no habilitado
       se rechaza.

El flujo es async por contrato (§4.4). Los tests lo ejecutan con
`async_to_sync` desde un test sync: `sync_to_async(thread_sensitive=True)`
regresa al hilo del test, de modo que la conexión de base de datos es la del
test y el rollback del fixture `db` funciona.
"""

import uuid

import pytest
from asgiref.sync import async_to_sync

from modules.eventos.domain.exceptions import (
    EdicionNoEncontradaError,
    EdicionPublicadaDuplicadaError,
    EdicionSlugDuplicadoError,
    EventoNoEncontradoError,
    ModuloNoHabilitadoError,
)
from modules.eventos.domain.models import Edicion
from modules.eventos.domain.schemas.edicion_schemas import EdicionCreateData
from modules.eventos.domain.services.flujos.edicion_flujo import EdicionFlujo


@pytest.fixture
def flujo(core_service, scope_service):
    """Flujo de escritura de ediciones."""
    return EdicionFlujo(core_service=core_service, scope_service=scope_service)


# ── Alta ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_nace_en_borrador(core_service, evento):
    data = EdicionCreateData(
        evento_id=evento.id,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
    )

    edicion = core_service.crear(data)

    assert edicion.estado == "BORRADOR"
    assert edicion.modulos_habilitados == []


@pytest.mark.django_db
def test_crear_con_evento_inexistente_es_error_de_dominio(core_service, db):
    data = EdicionCreateData(
        evento_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        nombre="Huerfana",
        slug="2026",
        anio=2026,
    )

    with pytest.raises(EventoNoEncontradoError):
        core_service.crear(data)


@pytest.mark.django_db
def test_crear_con_slug_duplicado_lo_traduce_el_flujo(flujo, evento):
    Edicion.objects.create(evento=evento, nombre="A", slug="2026", anio=2026)
    data = EdicionCreateData(
        evento_id=evento.id,
        nombre="B",
        slug="2026",
        anio=2027,
    )

    with pytest.raises(EdicionSlugDuplicadoError):
        async_to_sync(flujo.crear_edicion)(data)

    assert Edicion.objects.count() == 1


# ── Publicación ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_publicar_pasa_a_publicada(flujo, edicion_borrador):
    edicion = async_to_sync(flujo.publicar_edicion)(edicion_borrador.id)

    edicion.refresh_from_db()
    assert edicion.estado == "PUBLICADA"


@pytest.mark.django_db
def test_publicar_con_id_inexistente_no_publica_ninguna(flujo, db):
    with pytest.raises(EdicionNoEncontradaError):
        async_to_sync(flujo.publicar_edicion)(uuid.uuid4())

    assert Edicion.objects.count() == 0


@pytest.mark.django_db
def test_publicar_dos_ediciones_del_mismo_evento_es_conflicto(flujo, edicion_borrador):
    """CONCURRENCIA: la base de datos impide dos ediciones publicadas del mismo evento.

    La `UniqueConstraint` condicional es la autoridad final: aunque el código
    no compruebe nada, dos publicaciones del mismo evento no coexisten.
    """
    primera = Edicion.objects.create(
        evento=edicion_borrador.evento,
        nombre="Otra",
        slug="2027",
        anio=2027,
    )
    async_to_sync(flujo.publicar_edicion)(edicion_borrador.id)

    with pytest.raises(EdicionPublicadaDuplicadaError):
        async_to_sync(flujo.publicar_edicion)(primera.id)

    assert Edicion.objects.filter(estado="PUBLICADA").count() == 1


@pytest.mark.django_db
def test_publicar_es_idempotente_sobre_la_misma_edicion(flujo, edicion_borrador):
    async_to_sync(flujo.publicar_edicion)(edicion_borrador.id)
    async_to_sync(flujo.publicar_edicion)(edicion_borrador.id)

    assert Edicion.objects.filter(estado="PUBLICADA").count() == 1


# ── Cierre ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cerrar_pasa_a_cerrada(flujo, edicion_borrador):
    edicion = async_to_sync(flujo.cerrar_edicion)(edicion_borrador.id)

    edicion.refresh_from_db()
    assert edicion.estado == "CERRADA"


# ── Habilitación de módulos (RN-E02) ────────────────────────────────────────


@pytest.mark.django_db
def test_un_modulo_no_habilitado_se_rechaza(core_service, edicion_borrador):
    with pytest.raises(ModuloNoHabilitadoError):
        core_service.exigir_modulo(edicion_borrador, "inscripciones")


@pytest.mark.django_db
def test_un_modulo_habilitado_pasa(core_service, edicion_borrador):
    edicion_borrador.modulos_habilitados = ["inscripciones"]
    edicion_borrador.save()

    core_service.exigir_modulo(edicion_borrador, "inscripciones")
