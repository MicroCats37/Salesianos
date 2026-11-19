"""Contrato de multimedia (FREEZE-MD-1.0.0 · FR-06 §2).

GIVEN  el módulo `core.media` del backend objetivo
WHEN   se valida un archivo o se resuelve el protocolo multipart
THEN   se rechaza el tamaño, el tipo y la firma inválidos, y se rechaza el
       token ausente, el archivo huérfano y el token duplicado, con el código
       estable del contrato.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from core import media
from core.exceptions import (
    MediaArchivoHuerfanoError,
    MediaTamanoExcedidoError,
    MediaTokenDuplicadoError,
    MediaTokenNoResueltoError,
    MediaTipoNoPermitidoError,
)

# ── Fixtures de contenido ────────────────────────────────────────────────────

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 24
SVG_BYTES = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"


def _png(nombre="logo.png", contenido=None):
    return SimpleUploadedFile(
        nombre, contenido if contenido is not None else PNG_BYTES, content_type="image/png"
    )


def _jpeg(nombre="foto.jpg"):
    return SimpleUploadedFile(nombre, JPEG_BYTES, content_type="image/jpeg")


# ── Allowlist de tipo ────────────────────────────────────────────────────────


def test_la_allowlist_excluye_svg():
    assert "image/svg+xml" not in media.allowed_mime_types()
    assert media.allowed_mime_types() == {"image/jpeg", "image/png", "image/webp"}


def test_un_mime_fuera_de_la_allowlist_se_rechaza():
    archivo = SimpleUploadedFile("logo.svg", SVG_BYTES, content_type="image/svg+xml")

    with pytest.raises(MediaTipoNoPermitidoError) as exc:
        media.validar_archivo_media(archivo)

    assert exc.value.code == "MEDIA_TIPO_NO_PERMITIDO"
    assert exc.value.status_code == 400


def test_un_content_type_mentiroso_se_rechaza():
    """Los bytes son de un PNG pero se declaran como JPEG."""
    archivo = SimpleUploadedFile("logo.jpg", PNG_BYTES, content_type="image/jpeg")

    with pytest.raises(MediaTipoNoPermitidoError):
        media.validar_archivo_media(archivo)


def test_un_archivo_sin_firma_reconocible_se_rechaza():
    archivo = SimpleUploadedFile("logo.png", b"no soy una imagen", content_type="image/png")

    with pytest.raises(MediaTipoNoPermitidoError):
        media.validar_archivo_media(archivo)


# ── Tamaño ───────────────────────────────────────────────────────────────────


def test_un_archivo_sobre_el_tope_de_tamano_se_rechaza():
    with override_settings(MEDIA_MAX_SIZE_BYTES=10):
        archivo = _png(contenido=PNG_BYTES + b"0" * 64)

        with pytest.raises(MediaTamanoExcedidoError) as exc:
            media.validar_archivo_media(archivo)

    assert exc.value.code == "MEDIA_TAMANO_EXCEDIDO"
    assert exc.value.status_code == 413


def test_el_tope_por_defecto_es_de_cinco_mib():
    assert media.max_size_bytes() == 5 * 1024 * 1024


# ── Firma y extensión ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "contenido,mime_esperado",
    [
        (JPEG_BYTES, "image/jpeg"),
        (PNG_BYTES, "image/png"),
        (WEBP_BYTES, "image/webp"),
    ],
)
def test_la_firma_detecta_el_tipo_real(contenido, mime_esperado):
    assert media.detect_mime_type(contenido) == mime_esperado


def test_la_extension_se_deriva_del_tipo_detectado():
    validado = media.validar_archivo_media(_png())

    assert validado.mime_detectado == "image/png"
    assert validado.extension == ".png"


def test_el_nombre_del_usuario_no_se_usa_para_la_extension():
    validado = media.validar_archivo_media(_png(nombre="mi-logo-de-verano.png"))

    assert validado.extension == ".png"
    assert validado.nombre_original == "mi-logo-de-verano.png"


# ── Ruta de almacenamiento ───────────────────────────────────────────────────


def test_la_ruta_usa_dominio_entidad_y_uuid():
    ruta = media.construir_ruta_media("productos", 77, ".png")

    partes = ruta.split("/")
    assert partes[0] == "productos"
    assert partes[1] == "77"
    assert partes[2].endswith(".png")
    assert partes[2].split(".")[0] != "mi-logo-de-verano"


def test_la_ruta_rechaza_un_dominio_no_autorizado():
    with pytest.raises(ValueError):
        media.construir_ruta_media("cualquiera", 1, ".png")


def test_la_url_publica_usa_el_media_url():
    with override_settings(MEDIA_URL="/media/"):
        assert media.url_publica_media("productos/1/x.png") == "/media/productos/1/x.png"


# ── Protocolo multipart ──────────────────────────────────────────────────────


def test_un_token_ausente_se_rechaza():
    with pytest.raises(MediaTokenNoResueltoError) as exc:
        media.resolver_tokens_media({"logo": "file_abc"}, {})

    assert exc.value.code == "MEDIA_TOKEN_NO_RESUELTO"


def test_un_archivo_huerfano_se_rechaza():
    archivos = {"file_abc": _png(), "file_xyz": _png()}

    with pytest.raises(MediaArchivoHuerfanoError) as exc:
        media.resolver_tokens_media({"logo": "file_abc"}, archivos)

    assert exc.value.code == "MEDIA_ARCHIVO_HUERFANO"


def test_un_token_duplicado_en_el_payload_se_rechaza():
    archivos = {"file_abc": _png()}

    with pytest.raises(MediaTokenDuplicadoError) as exc:
        media.resolver_tokens_media({"logo": "file_abc", "banner": "file_abc"}, archivos)

    assert exc.value.code == "MEDIA_TOKEN_DUPLICADO"


def test_un_token_repetido_en_listas_anidadas_se_rechaza():
    archivos = {"file_abc": _png()}

    with pytest.raises(MediaTokenDuplicadoError):
        media.resolver_tokens_media(
            {"galeria": [{"imagen": "file_abc"}, {"imagen": "file_abc"}]}, archivos
        )


def test_una_parte_de_archivo_sin_token_se_rechaza():
    class _Archivos:
        def getlist(self, _key):
            return [SimpleUploadedFile("sin-token.png", PNG_BYTES, content_type="image/png")]

    with pytest.raises(MediaTokenNoResueltoError):
        media.parsear_archivos_media(_Archivos())


def test_una_parte_de_archivo_con_el_convencion_se_resuelve():
    class _Archivos:
        def getlist(self, _key):
            return [
                SimpleUploadedFile(
                    "file_abc___logo-real.png", PNG_BYTES, content_type="image/png"
                )
            ]

    archivos = media.parsear_archivos_media(_Archivos())

    assert list(archivos) == ["file_abc"]
    assert archivos["file_abc"].name == "logo-real.png"


def test_dos_partes_con_el_mismo_token_se_rechazan():
    class _Archivos:
        def getlist(self, _key):
            return [
                SimpleUploadedFile("file_abc___a.png", PNG_BYTES, content_type="image/png"),
                SimpleUploadedFile("file_abc___b.png", PNG_BYTES, content_type="image/png"),
            ]

    with pytest.raises(MediaTokenDuplicadoError):
        media.parsear_archivos_media(_Archivos())


def test_la_resolucion_devuelve_el_archivo_de_cada_token():
    archivo = _png()
    resueltos = media.resolver_tokens_media({"logo": "file_abc"}, {"file_abc": archivo})

    assert resueltos == {"file_abc": archivo}


# ── Limpieza ─────────────────────────────────────────────────────────────────


def test_la_limpieza_borra_el_archivo_escrito(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        ruta = "productos/1/x.png"
        absoluta = media.ruta_absoluta_media(ruta)
        absoluta.parent.mkdir(parents=True, exist_ok=True)
        absoluta.write_bytes(PNG_BYTES)

        eliminadas = media.limpiar_archivos_media([ruta])

        assert eliminadas == [ruta]
        assert not absoluta.exists()


def test_la_limpieza_es_idempotente(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        assert media.limpiar_archivos_media(["productos/1/no-existe.png"]) == []
