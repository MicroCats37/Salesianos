"""Limpieza de media de patrocinadores: rollback, reemplazo y borrado.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`

Cubre los TRES caminos obligatorios de limpieza de FR-06 §2.5:

- **rollback**: si la operación falla DESPUÉS de escribir un archivo, el
  archivo se borra (la base de datos se revierte sola; el volumen de media no);
- **reemplazo**: el archivo anterior se borra DESPUÉS de que el nuevo quedó
  persistido; si el reemplazo falla, el anterior sigue en su sitio;
- **borrado**: al borrar una imagen o el patrocinador, sus archivos se borran
  (el logo incluido).

Y las reglas de coherencia del dominio: alcance de edición, unicidad del slug
por edición, galería ordenada y visibilidad.
"""

import pytest
from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.patrocinadores.domain.constants import MAX_IMAGENES_GALERIA
from modules.patrocinadores.domain.exceptions import (
    GaleriaPatrocinadorInvalidaError,
)
from modules.patrocinadores.domain.models import Patrocinador, PatrocinadorImagen
from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
    ArchivoPatrocinadorUploadData,
    ImagenPatrocinadorData,
    LogoPatrocinadorData,
    PatrocinadorCreateData,
)
from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
    PatrocinadorCoreService,
)
from modules.patrocinadores.domain.services.core.patrocinador_media_service import (
    PatrocinadorMediaService,
)
from modules.patrocinadores.domain.services.flujos.patrocinador_flujo import (
    PatrocinadorFlujo,
)
from modules.patrocinadores.tests.fixtures.patrocinadores_fixtures import PNG_MINIMO


# ── Dobles de test ──────────────────────────────────────────────────────────


class MediaServiceQueFalla(PatrocinadorMediaService):
    """Doble que falla al escribir la SEGUNDA imagen.

    Permite ejercitar el rollback de media: el primer archivo YA se escribió
    en disco y la operación falla después.
    """

    def __init__(self, falla_en: int = 2):
        self.falla_en = falla_en
        self.escrituras = 0

    def escribir_imagen(self, patrocinador, imagen, orden, rutas_escritas):
        self.escrituras += 1
        if self.escrituras == self.falla_en:
            raise RuntimeError("fallo simulado al escribir la imagen")
        return super().escribir_imagen(patrocinador, imagen, orden, rutas_escritas)


def _upload(token: str = "file_aaa111") -> ArchivoPatrocinadorUploadData:
    """Un archivo de imagen YA validado (lo que hace el borde HTTP)."""
    return ArchivoPatrocinadorUploadData(
        token=token,
        archivo=SimpleUploadedFile("imagen.png", PNG_MINIMO, content_type="image/png"),
        mime_detectado="image/png",
        extension=".png",
        tamano=len(PNG_MINIMO),
        nombre_original="imagen.png",
    )


def _imagen(token: str = "file_aaa111", **extra) -> ImagenPatrocinadorData:
    return ImagenPatrocinadorData(token=token, upload=_upload(token), **extra)


def _logo(token: str = "file_logo111") -> LogoPatrocinadorData:
    return LogoPatrocinadorData(token=token, upload=_upload(token))


def _alta(edicion_id, logo=None, imagenes=None, **extra) -> PatrocinadorCreateData:
    payload = {
        "edicion_id": edicion_id,
        "nombre": "Colegio San Juan Bosco",
        "slug": "colegio-san-juan-bosco",
        "descripcion": "Patrocinador de la edición 2026.",
        "visible": True,
    }
    payload.update(extra)
    return PatrocinadorCreateData(
        logo=logo,
        imagenes=imagenes or [],
        **payload,
    )


def _archivos_en_el_volumen(media_root) -> list:
    """Los archivos (NO los directorios) que quedan en el volumen."""
    return [ruta for ruta in media_root.rglob("*") if ruta.is_file()]


# ── Rollback ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_un_rollback_deja_el_volumen_sin_residuos(edicion_publicada, media_root):
    """GIVEN un fallo DESPUÉS de escribir el primer archivo
    THEN   el archivo se borra, la fila no existe y el volumen queda vacío.
    """
    media = MediaServiceQueFalla(falla_en=2)
    flujo = PatrocinadorFlujo(core_service=PatrocinadorCoreService(), media_service=media)

    with pytest.raises(RuntimeError):
        async_to_sync(flujo.crear_patrocinador)(
            _alta(
                edicion_publicada.id,
                logo=_logo(),
                imagenes=[_imagen(), _imagen("file_bbb222")],
            )
        )

    assert Patrocinador.objects.count() == 0
    assert PatrocinadorImagen.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_una_alta_exitosa_persiste_los_archivos(edicion_publicada, media_root):
    """GIVEN un alta sin fallos · WHEN se crea el patrocinador
    THEN   los archivos quedan en el volumen, en la ruta congelada.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )

    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, logo=_logo(), imagenes=[_imagen()])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    imagen = patrocinador.imagenes.first()
    assert imagen is not None
    assert (media_root / imagen.imagen.name).exists()
    assert (media_root / patrocinador.logo.name).exists()
    assert imagen.imagen.name.startswith(f"patrocinadores/{patrocinador.id}/")
    assert patrocinador.logo.name.startswith(f"patrocinadores/{patrocinador.id}/")


# ── Reemplazo ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_reemplazar_el_logo_borra_el_archivo_anterior_despues_del_nuevo(
    edicion_publicada, media_root
):
    """GIVEN un logo persistido · WHEN se reemplaza su archivo
    THEN   el archivo nuevo existe, el anterior se borró y la fila conserva
            su identificador.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, logo=_logo(), imagenes=[_imagen()])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    ruta_previa = patrocinador.logo.name
    assert (media_root / ruta_previa).exists()

    async_to_sync(flujo.reemplazar_logo)(patrocinador.id, _upload("file_nuevo"))

    patrocinador.refresh_from_db()
    assert patrocinador.logo.name != ruta_previa
    assert (media_root / patrocinador.logo.name).exists()
    assert not (media_root / ruta_previa).exists()
    assert Patrocinador.objects.count() == 1


@pytest.mark.django_db
def test_un_reemplazo_fallido_conserva_el_archivo_anterior(edicion_publicada, media_root):
    """GIVEN un reemplazo que falla · THEN el archivo anterior sigue en su
    sitio y no queda ningún archivo nuevo.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, logo=_logo(), imagenes=[_imagen()])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    ruta_previa = patrocinador.logo.name

    class MediaQueFalla(PatrocinadorMediaService):
        def reemplazar_logo(self, patrocinador, upload, rutas_escritas):
            raise RuntimeError("fallo simulado al reemplazar")

    flujo_fallido = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=MediaQueFalla()
    )
    with pytest.raises(RuntimeError):
        async_to_sync(flujo_fallido.reemplazar_logo)(patrocinador.id, _upload("file_nueva"))

    patrocinador.refresh_from_db()
    assert patrocinador.logo.name == ruta_previa
    assert (media_root / ruta_previa).exists()
    assert len(list(media_root.rglob("*.png"))) == 2  # el logo y la imagen


@pytest.mark.django_db
def test_reemplazar_una_imagen_de_la_galeria(edicion_publicada, media_root):
    """GIVEN una imagen persistida · WHEN se reemplaza su archivo
    THEN   el archivo nuevo existe, el anterior se borró y el ORDEN se conserva.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, imagenes=[_imagen(), _imagen("file_bbb222")])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    imagen = patrocinador.imagenes.order_by("orden", "id").first()
    ruta_previa = imagen.imagen.name
    assert (media_root / ruta_previa).exists()

    async_to_sync(flujo.reemplazar_imagen)(patrocinador.id, imagen.id, _upload("file_nueva"))

    imagen.refresh_from_db()
    assert imagen.imagen.name != ruta_previa
    assert (media_root / imagen.imagen.name).exists()
    assert not (media_root / ruta_previa).exists()
    assert imagen.orden == 0
    assert PatrocinadorImagen.objects.count() == 2


# ── Borrado ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_borrar_una_imagen_borra_su_archivo(edicion_publicada, media_root):
    """GIVEN un patrocinador con una imagen · WHEN se borra la imagen
    THEN   la fila desaparece y el archivo también.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, logo=_logo(), imagenes=[_imagen()])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    imagen = patrocinador.imagenes.first()
    ruta = imagen.imagen.name
    assert (media_root / ruta).exists()

    async_to_sync(flujo.eliminar_imagen)(patrocinador.id, imagen.id)

    assert PatrocinadorImagen.objects.count() == 0
    assert not (media_root / ruta).exists()
    # El logo NO se toca: es otro recurso.
    assert (media_root / patrocinador.logo.name).exists()


@pytest.mark.django_db
def test_borrar_el_patrocinador_borra_el_logo_y_sus_archivos(edicion_publicada, media_root):
    """GIVEN un patrocinador con logo y dos imágenes · WHEN se borra
    THEN   ni la fila ni los archivos quedan en el volumen.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(
            edicion_publicada.id,
            logo=_logo(),
            imagenes=[_imagen(), _imagen("file_bbb222")],
        )
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    rutas = [imagen.imagen.name for imagen in patrocinador.imagenes.all()]
    rutas.append(patrocinador.logo.name)
    assert len(rutas) == 3

    async_to_sync(flujo.eliminar_patrocinador)(patrocinador.id)

    assert Patrocinador.objects.count() == 0
    assert PatrocinadorImagen.objects.count() == 0
    for ruta in rutas:
        assert not (media_root / ruta).exists()
    assert _archivos_en_el_volumen(media_root) == []


# ── Coherencia del dominio ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_una_galeria_demasiado_grande_se_rechaza(edicion_publicada, media_root):
    """GIVEN una galería con más imágenes que el tope declarado
    THEN   se rechaza con GALERIA_PATROCINADOR_INVALIDA y NO se escribe nada.
    """
    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )

    imagenes = [_imagen(f"file_{indice:04d}") for indice in range(MAX_IMAGENES_GALERIA + 1)]

    with pytest.raises(GaleriaPatrocinadorInvalidaError):
        async_to_sync(flujo.crear_patrocinador)(_alta(edicion_publicada.id, imagenes=imagenes))

    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_el_orden_de_la_galeria_se_puede_fijar(edicion_publicada, media_root):
    """GIVEN dos imágenes · WHEN se fija su orden explícito
    THEN   el orden canónico cambia y la galería conserva su contenido.
    """
    from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
        PatrocinadorOrdenImagenData,
    )

    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, imagenes=[_imagen(), _imagen("file_bbb222")])
    )

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    imagenes = list(patrocinador.imagenes.order_by("orden", "id"))
    assert [imagen.orden for imagen in imagenes] == [0, 1]

    resultado = async_to_sync(flujo.reordenar_galeria)(
        patrocinador.id,
        [
            PatrocinadorOrdenImagenData(imagen_id=imagenes[1].id, orden=0),
            PatrocinadorOrdenImagenData(imagen_id=imagenes[0].id, orden=1),
        ],
    )

    assert [imagen.orden for imagen in resultado.imagenes] == [0, 1]
    assert [imagen.id for imagen in resultado.imagenes] == [
        imagenes[1].id,
        imagenes[0].id,
    ]


@pytest.mark.django_db
def test_una_imagen_de_otro_patrocinador_se_rechaza(edicion_publicada, media_root):
    """GIVEN una imagen que NO pertenece al patrocinador
    THEN   se rechaza con PATROCINADOR_IMAGEN_NO_ENCONTRADA: el orden NUNCA
            cruza el alcance.
    """
    from modules.patrocinadores.domain.exceptions import (
        PatrocinadorImagenNoEncontradaError,
    )

    flujo = PatrocinadorFlujo(
        core_service=PatrocinadorCoreService(), media_service=PatrocinadorMediaService()
    )
    async_to_sync(flujo.crear_patrocinador)(
        _alta(edicion_publicada.id, imagenes=[_imagen()])
    )
    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")

    otro = Patrocinador.objects.create(
        edicion=edicion_publicada,
        nombre="Otro patrocinador",
        slug="otro-patrocinador",
    )
    imagen_ajena = PatrocinadorImagen.objects.create(
        patrocinador=otro, imagen="patrocinadores/x/ajena.png", orden=0
    )

    with pytest.raises(PatrocinadorImagenNoEncontradaError):
        async_to_sync(flujo.eliminar_imagen)(patrocinador.id, imagen_ajena.id)
