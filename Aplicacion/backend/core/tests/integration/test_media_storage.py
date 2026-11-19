"""Almacenamiento de media del backend objetivo (A0 · FREEZE-MD-1.0.0).

GIVEN  la configuración de `STORAGES` del objetivo y el volumen persistente
       de media (`MEDIA_ROOT`)
WHEN   se resuelve el almacenamiento por defecto y se escribe y limpia un
       archivo en un volumen de prueba temporal
THEN   `default_storage` EXISTE y es local y persistente, el archivo se
       escribe dentro del volumen y la limpieza deja CERO residuos.

Por qué este test existe (reconciliación A0 de DOM-04, petición A0-04):

`STORAGES` declaraba SÓLO la entrada `staticfiles`. Django 5 necesita también
la entrada `default`: sin ella `default_storage` no existe y **ningún módulo
puede escribir media** — el error es `InvalidStorageError: Could not find
config for 'default' in settings.STORAGES`, no un fallo de negocio. Los
módulos que tienen un `ImageField` (`marketplace`) y los que consultan
`default_storage` (`ProductoMediaService`) quedan bloqueados.

La entrada `default` debe ser el `FileSystemStorage` LOCAL de Django: escribe
bajo `MEDIA_ROOT`, que es el VOLUMEN PERSISTENTE del contrato de media
(FR-06 §2.1). Este test NO inventa almacenamiento en la nube, ni rutas, ni
credenciales: comprueba que lo declarado es local y que el ciclo
escritura → limpieza no deja residuos.
"""

from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage, storages
from django.test import override_settings

from core.media import limpiar_archivos_media


#: Backend local de Django: escribe bajo `MEDIA_ROOT` (volumen persistente).
BACKEND_LOCAL = "django.core.files.storage.FileSystemStorage"


def _residuos(raiz: Path) -> list[Path]:
    """Archivos que quedan dentro del volumen."""
    if not raiz.exists():
        return []
    return sorted(ruta for ruta in raiz.rglob("*") if ruta.is_file())


# ── La configuración ─────────────────────────────────────────────────────────


def test_el_almacenamiento_por_defecto_esta_declarado():
    """`STORAGES` declara la entrada `default` además de `staticfiles`."""
    declarados = settings.STORAGES

    assert "default" in declarados, (
        "Sin la entrada `default` de `STORAGES` no existe `default_storage` "
        "y ningún módulo puede escribir media."
    )
    assert declarados["default"]["BACKEND"] == BACKEND_LOCAL


def test_el_almacenamiento_por_defecto_es_local():
    """El backend declarado es el `FileSystemStorage` local de Django."""
    backend = settings.STORAGES["default"]["BACKEND"]

    assert backend == BACKEND_LOCAL
    assert issubclass(storages["default"].__class__, FileSystemStorage)


def test_el_volumen_por_defecto_es_el_media_root_persistente():
    """`default_storage` escribe bajo `MEDIA_ROOT`: el volumen persistente."""
    assert str(default_storage.location) == str(settings.MEDIA_ROOT)
    assert str(settings.MEDIA_ROOT) == str(settings.BASE_DIR / "media")


def test_default_storage_se_puede_resolver():
    """El defecto original era un `InvalidStorageError` al resolverlo."""
    storage = storages["default"]

    assert storage is not None
    assert hasattr(storage, "save")
    assert hasattr(storage, "delete")


# ── Escritura y limpieza sobre un volumen de prueba temporal ─────────────────


@pytest.fixture
def volumen_temporal(tmp_path):
    """Volumen de media temporal: `MEDIA_ROOT` y `STORAGES` apuntan a él.

    Se sobreescribe `STORAGES` (y no sólo `MEDIA_ROOT`) porque Django sólo
    reinicia la caché de los almacenamientos cuando cambia `STORAGES`,
    `STATIC_ROOT` o `STATIC_URL`. El volumen real NO se toca jamás.
    """
    raiz = tmp_path / "media"
    raiz.mkdir()

    storages_de_prueba = {
        "default": {
            "BACKEND": BACKEND_LOCAL,
            "OPTIONS": {"location": str(raiz)},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    with override_settings(STORAGES=storages_de_prueba, MEDIA_ROOT=str(raiz)):
        yield raiz


def test_un_archivo_se_escribe_en_el_volumen_persistente(volumen_temporal):
    """GIVEN el volumen de prueba
    WHEN  se escribe un archivo con `default_storage`
    THEN  el archivo existe DENTRO del volumen, en la ruta pedida.
    """
    ruta = "productos/1/abc123.png"

    nombre = default_storage.save(ruta, ContentFile(b"contenido-de-prueba"))

    assert nombre == ruta
    assert (volumen_temporal / ruta).is_file()
    assert _residuos(volumen_temporal) == [volumen_temporal / ruta]


def test_la_limpieza_deja_cero_residuos(volumen_temporal):
    """GIVEN un archivo escrito en el volumen
    WHEN  se limpia con el helper del contrato de media
    THEN  no queda NINGÚN archivo en el volumen y el storage lo confirma.
    """
    ruta = "productos/1/abc123.png"
    default_storage.save(ruta, ContentFile(b"contenido-de-prueba"))

    eliminadas = limpiar_archivos_media([ruta])

    assert eliminadas == [ruta]
    assert _residuos(volumen_temporal) == []
    assert default_storage.exists(ruta) is False


def test_limpiar_un_archivo_inexistente_no_falla(volumen_temporal):
    """La limpieza es best-effort: nunca propaga el fallo de un borrado."""
    eliminadas = limpiar_archivos_media(["productos/1/no-existe.png"])

    assert eliminadas == []
    assert _residuos(volumen_temporal) == []
