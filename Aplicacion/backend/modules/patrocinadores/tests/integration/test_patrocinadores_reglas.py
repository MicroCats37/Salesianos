"""Reglas de dominio de los patrocinadores: alcance, visibilidad y orden.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0`

Cubre las reglas ESTRUCTURALES del módulo:

- el alcance es la EDICIÓN (RN-E01) y el cliente NUNCA la elige;
- el slug es único POR EDICIÓN (la base de datos es la autoridad);
- la visibilidad es un hecho del patrocinador (ADM-21);
- la galería tiene un orden canónico `orden ASC, id ASC` (FR-06 §2.6);
- un módulo lógico deshabilitado no expone catálogo ni escrituras (RN-E02);
- la degradación por archivo ausente (FR-06 §2.7).
"""

import pytest
from asgiref.sync import async_to_sync
from django.db import IntegrityError, transaction

from modules.patrocinadores.domain.exceptions import ModuloNoHabilitadoError
from modules.patrocinadores.domain.models import Patrocinador, PatrocinadorImagen
from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
    PatrocinadorUpdateData,
)
from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
    PatrocinadorCoreService,
)
from modules.patrocinadores.domain.services.flujos.patrocinador_flujo import (
    PatrocinadorFlujo,
)
from modules.patrocinadores.domain.services.orchestrators.patrocinador_orchestrator import (
    PatrocinadorOrchestrator,
)
from modules.patrocinadores.infrastructure.services.alcance_edicion_eventos import (
    AlcanceEdicionEventos,
)


def _orquestador() -> PatrocinadorOrchestrator:
    """Un orquestador con los servicios REALES (sin dobles)."""
    core = PatrocinadorCoreService()
    return PatrocinadorOrchestrator(
        core_service=core,
        flujo=PatrocinadorFlujo(core_service=core, media_service=core.media_service),
        alcance=AlcanceEdicionEventos(),
    )


# ── Alcance de edición ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_slug_es_unico_por_edicion(edicion_publicada, edicion_otra):
    """GIVEN dos patrocinadores con el mismo slug en ediciones DISTINTAS
    THEN   ambos existen: la unicidad es POR EDICIÓN, no global.
    """
    Patrocinador.objects.create(
        edicion=edicion_publicada, nombre="Colegio", slug="colegio"
    )
    Patrocinador.objects.create(edicion=edicion_otra, nombre="Colegio", slug="colegio")
    assert Patrocinador.objects.filter(slug="colegio").count() == 2


@pytest.mark.django_db
def test_el_slug_es_unico_dentro_de_la_edicion(edicion_publicada):
    """GIVEN dos patrocinadores con el mismo slug en la MISMA edición
    THEN   la base de datos lo rechaza: la base es la autoridad.
    """
    Patrocinador.objects.create(
        edicion=edicion_publicada, nombre="Colegio", slug="colegio"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Patrocinador.objects.create(
                edicion=edicion_publicada, nombre="Colegio 2", slug="colegio"
            )


@pytest.mark.django_db
def test_el_selector_acentua_el_ambito_de_edicion(edicion_publicada, edicion_otra):
    """GIVEN un patrocinador de OTRA edición · WHEN se busca por slug
    THEN   no se encuentra: el alcance es explícito, nunca implícito.
    """
    from modules.patrocinadores.domain.selectors.patrocinador_selector import (
        PatrocinadorSelector,
    )

    Patrocinador.objects.create(edicion=edicion_otra, nombre="Colegio", slug="colegio")
    selector = PatrocinadorSelector()

    assert selector.obtener_por_slug(edicion_otra.id, "colegio") is not None
    assert selector.obtener_por_slug(edicion_publicada.id, "colegio") is None


@pytest.mark.django_db
def test_el_modulo_deshabilitado_no_expone_patrocinadores(edicion_sin_patrocinadores):
    """GIVEN una edición con el módulo `patrocinadores` DESHABILITADO
    THEN   la operación se rechaza con MODULO_NO_HABILITADO (RN-E02).
    """
    with pytest.raises(ModuloNoHabilitadoError):
        async_to_sync(_orquestador().listar_por_edicion)()


# ── Visibilidad ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_la_visibilidad_es_un_hecho_del_patrocinador(edicion_publicada, patrocinador):
    """GIVEN un patrocinador invisible · WHEN se lista el consumo público
    THEN   NO aparece; el catálogo de administración sí lo ve.
    """
    from modules.patrocinadores.domain.selectors.patrocinador_selector import (
        PatrocinadorSelector,
    )

    patrocinador.visible = False
    patrocinador.save(update_fields=["visible"])

    selector = PatrocinadorSelector()
    assert selector.listar_por_edicion(edicion_publicada.id, visible=True) == []
    assert len(selector.listar_por_edicion(edicion_publicada.id, visible=False)) == 1
    assert len(selector.listar_por_edicion(edicion_publicada.id)) == 1


@pytest.mark.django_db
def test_la_visibilidad_se_puede_cambiar(edicion_publicada, patrocinador):
    """GIVEN un patrocinador visible · WHEN se oculta
    THEN   el hecho cambia y el resultado lo refleja.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(),
        media_service=PatrocinadorCoreService().media_service,
    )

    resultado = async_to_sync(flujo.actualizar_patrocinador)(
        patrocinador.id, PatrocinadorUpdateData(visible=False)
    )

    assert resultado.visible is False
    patrocinador.refresh_from_db()
    assert patrocinador.visible is False


@pytest.mark.django_db
def test_actualizar_la_ficha_no_toca_los_archivos(edicion_publicada, patrocinador):
    """GIVEN un patrocinador con logo · WHEN se actualiza su descripción
    THEN   el logo sigue siendo el mismo.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(),
        media_service=PatrocinadorCoreService().media_service,
    )

    resultado = async_to_sync(flujo.actualizar_patrocinador)(
        patrocinador.id,
        PatrocinadorUpdateData(nombre="Colegio Juan Bosco", descripcion="Nuevo texto."),
    )

    assert resultado.nombre == "Colegio Juan Bosco"
    assert resultado.descripcion == "Nuevo texto."
    patrocinador.refresh_from_db()
    assert patrocinador.logo.name == ""


# ── Orden de la galería ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_orden_de_la_galeria_es_orden_por_id(patrocinador):
    """FR-06 §2.6: el orden canónico es `orden ASC, id ASC`."""
    primera = PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/a.png", orden=5
    )
    segunda = PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/b.png", orden=1
    )
    assert list(patrocinador.imagenes.all()) == [segunda, primera]


# ── Degradación ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_un_archivo_ausente_degrada_con_aviso(patrocinador, media_root):
    """GIVEN una imagen cuyo archivo ya no está en el volumen
    THEN   viaja con `disponible = False` y `url = None`: no hay 500 ni hueco
            oculto (FR-06 §2.7).
    """
    PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/ausente.png", orden=0
    )

    core = PatrocinadorCoreService()
    resultado = core.result_de(patrocinador)

    assert len(resultado.imagenes) == 1
    assert resultado.imagenes[0].disponible is False
    assert resultado.imagenes[0].url is None


@pytest.mark.django_db
def test_un_patrocinador_sin_logo_no_inventa_un_logo(patrocinador):
    """GIVEN un patrocinador sin logo · WHEN se proyecta
    THEN   el logo viaja como `None`, no como una URL vacía.
    """
    core = PatrocinadorCoreService()
    resultado = core.result_de(patrocinador)
    assert resultado.logo is None


# ── Autoridades del dominio ────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_result_expone_la_galeria_ordenada_y_la_visibilidad(
    edicion_publicada, patrocinador
):
    """GIVEN un patrocinador con dos imágenes · WHEN se proyecta al result
    THEN   la galería viaja ORDENADA y la visibilidad como un hecho.
    """
    PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/primera.png", orden=1
    )
    PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/segunda.png", orden=0
    )

    core = PatrocinadorCoreService()
    resultado = core.result_de(patrocinador)

    assert [imagen.orden for imagen in resultado.imagenes] == [0, 1]
    assert resultado.visible is True
    assert resultado.edicion_id == edicion_publicada.id
    assert resultado.edicion_nombre == edicion_publicada.nombre
