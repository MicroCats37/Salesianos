"""Protocolo multipart de media de patrocinadores: éxito y fallos.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`

Cubre el protocolo COMPLETO (FR-06 §2.4) sobre la ruta `RT-MD-02`:

- alta JSON (sin imágenes) y alta multipart (con logo y galería ordenada);
- token ausente (`MEDIA_TOKEN_NO_RESUELTO`);
- archivo huérfano (`MEDIA_ARCHIVO_HUERFANO`);
- token duplicado (`MEDIA_TOKEN_DUPLICADO`);
- firma de contenido inválida (`MEDIA_TIPO_NO_PERMITIDO`);
- tamaño excedido (`MEDIA_TAMANO_EXCEDIDO`);
- NINGÚN archivo residual en el volumen de media tras un rechazo;
- el permiso `Administrador` y la envoltura de respuesta congelada.

El módulo CONSUME el protocolo de `core/media.py`: no hay una segunda
implementación del matching de tokens (el paquete DOM-08 lo demuestra con un
test de contrato).
"""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.patrocinadores.domain.models import Patrocinador
from modules.patrocinadores.tests.factories import (
    make_imagen_payload,
    make_patrocinador_payload,
)
from modules.patrocinadores.tests.fixtures.patrocinadores_fixtures import (
    JPEG_MINIMO,
    PNG_MINIMO,
)

pytestmark = pytest.mark.urls("modules.patrocinadores.tests.urls_patrocinadores")


def _parte(token: str, contenido: bytes, nombre: str, content_type: str):
    """Una parte `files` con el nombre `<token>___<realname>`."""
    return SimpleUploadedFile(
        f"{token}___{nombre}",
        contenido,
        content_type=content_type,
    )


def _archivos_en_el_volumen(media_root) -> list:
    """Los archivos (NO los directorios) que quedan en el volumen."""
    return [ruta for ruta in media_root.rglob("*") if ruta.is_file()]


# ── Éxito ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_alta_json_sin_imagenes(client, edicion_publicada, token_admin, media_root):
    """GIVEN un payload JSON sin archivos · WHEN se crea el patrocinador
    THEN   200 con la envoltura congelada y el patrocinador persistido.
    """
    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["nombre"] == "Colegio San Juan Bosco"
    assert cuerpo["data"]["slug"] == "colegio-san-juan-bosco"
    assert cuerpo["data"]["visible"] is True
    assert cuerpo["data"]["logo"] is None
    assert cuerpo["data"]["imagenes"] == []
    assert Patrocinador.objects.filter(slug="colegio-san-juan-bosco").count() == 1


@pytest.mark.django_db
def test_alta_multipart_guarda_el_logo_y_la_galeria_en_orden(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un logo y dos imágenes con sus tokens · WHEN se crea el
    patrocinador THEN   el logo y la galería persisten ORDENADOS y los
    archivos quedan en el volumen con la ruta congelada.
    """
    token_logo = "file_logo111"
    token_a = "file_aaa111"
    token_b = "file_bbb222"
    payload = make_patrocinador_payload(
        logo=token_logo,
        imagenes=[
            make_imagen_payload(token_a, texto_alternativo="Portada"),
            make_imagen_payload(token_b, texto_alternativo="Fachada"),
        ],
    )

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [
                _parte(token_logo, PNG_MINIMO, "logo.png", "image/png"),
                _parte(token_a, PNG_MINIMO, "uno.png", "image/png"),
                _parte(token_b, JPEG_MINIMO, "dos.jpg", "image/jpeg"),
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]

    assert datos["logo"]["url"]
    assert datos["logo"]["disponible"] is True

    imagenes = datos["imagenes"]
    assert [imagen["orden"] for imagen in imagenes] == [0, 1]
    assert imagenes[0]["texto_alternativo"] == "Portada"
    assert imagenes[1]["texto_alternativo"] == "Fachada"
    assert all(imagen["url"] for imagen in imagenes)
    assert all(imagen["disponible"] for imagen in imagenes)

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    assert patrocinador.imagenes.count() == 2
    assert [imagen.orden for imagen in patrocinador.imagenes.all()] == [0, 1]
    assert patrocinador.logo.name

    # La ruta es `patrocinadores/<patrocinador_id>/<uuid><ext>` (FR-06 §2.2).
    for imagen in patrocinador.imagenes.all():
        assert imagen.imagen.name.startswith(f"patrocinadores/{patrocinador.id}/")
        assert imagen.imagen.name.endswith(".png") or imagen.imagen.name.endswith(".jpg")
    assert patrocinador.logo.name.startswith(f"patrocinadores/{patrocinador.id}/")


@pytest.mark.django_db
def test_el_cliente_nunca_elige_la_edicion(client, edicion_publicada, token_admin, media_root):
    """GIVEN un payload SIN edition_id · WHEN se crea el patrocinador
    THEN   la edición la resuelve el servidor: es la edición vigente.
    """
    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    assert str(patrocinador.edicion_id) == str(edicion_publicada.id)
    assert respuesta.json()["data"]["edicion_id"] == str(edicion_publicada.id)


# ── Rechazos del protocolo ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_token_sin_archivo_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN un token en el payload SIN parte de archivo
    THEN   400 MEDIA_TOKEN_NO_RESUELTO y ningún archivo en el volumen.
    """
    payload = make_patrocinador_payload(imagenes=[make_imagen_payload("file_aaa111")])

    respuesta = client.post(
        "/api/patrocinadores",
        data={"data": json.dumps(payload)},
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "MEDIA_TOKEN_NO_RESUELTO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_logo_sin_archivo_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN un logo declarado SIN parte de archivo
    THEN   400 MEDIA_TOKEN_NO_RESUELTO: el logo usa el MISMO protocolo.
    """
    payload = make_patrocinador_payload(logo="file_logo111")

    respuesta = client.post(
        "/api/patrocinadores",
        data={"data": json.dumps(payload)},
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TOKEN_NO_RESUELTO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_archivo_huerfano_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN una parte de archivo que el payload NO referencia
    THEN   400 MEDIA_ARCHIVO_HUERFANO y ningún residuo en el volumen.
    """
    payload = make_patrocinador_payload()

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [_parte("file_huerfano", PNG_MINIMO, "huerfano.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_ARCHIVO_HUERFANO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_token_duplicado_en_el_payload_se_rechaza(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN el MISMO token dos veces en el payload (logo y galería)
    THEN   400 MEDIA_TOKEN_DUPLICADO: el matching es exactamente una vez.
    """
    token = "file_aaa111"
    payload = make_patrocinador_payload(
        logo=token,
        imagenes=[make_imagen_payload(token)],
    )

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [_parte(token, PNG_MINIMO, "uno.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TOKEN_DUPLICADO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_dos_partes_con_el_mismo_token_se_rechazan(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN dos partes de archivo con el MISMO token
    THEN   400 MEDIA_TOKEN_DUPLICADO: el token no puede resolver dos veces.
    """
    token = "file_aaa111"
    payload = make_patrocinador_payload(imagenes=[make_imagen_payload(token)])

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [
                _parte(token, PNG_MINIMO, "uno.png", "image/png"),
                _parte(token, PNG_MINIMO, "otro.png", "image/png"),
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TOKEN_DUPLICADO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_firma_de_contenido_invalida_se_rechaza(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un archivo que DECLARA `image/png` pero no tiene firma de imagen
    THEN   400 MEDIA_TIPO_NO_PERMITIDO y ningún residuo.
    """
    token = "file_aaa111"
    payload = make_patrocinador_payload(imagenes=[make_imagen_payload(token)])

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [
                _parte(token, b"esto no es una imagen" * 10, "mentira.png", "image/png")
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TIPO_NO_PERMITIDO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_tamano_excedido_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN un archivo que excede el tope de tamaño
    THEN   413 MEDIA_TAMANO_EXCEDIDO y ningún residuo.
    """
    token = "file_aaa111"
    payload = make_patrocinador_payload(imagenes=[make_imagen_payload(token)])
    grande = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 1024)

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [_parte(token, grande, "grande.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 413, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TAMANO_EXCEDIDO"
    assert Patrocinador.objects.count() == 0
    assert _archivos_en_el_volumen(media_root) == []


@pytest.mark.django_db
def test_payload_invalido_responde_422_con_field_errors(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un payload que no valida contra el schema
    THEN   422 con `field_errors` y ningún patrocinador creado.
    """
    payload = make_patrocinador_payload(slug="Colegio San Juan Bosco")

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 422, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "VALIDATION_ERROR"
    assert any(error["field"] == "slug" for error in cuerpo["error"]["field_errors"])
    assert Patrocinador.objects.count() == 0


@pytest.mark.django_db
def test_una_texto_opcional_vacio_se_guarda_como_vacio(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un payload con `descripcion` y `sitio_web` VACÍOS
    THEN   200: la cadena vacía es un VALOR (el valor por defecto del
            contrato), no un `null` que rompa la validación de tipo.
    """
    payload = make_patrocinador_payload(descripcion="", sitio_web="")

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["descripcion"] == ""
    assert datos["sitio_web"] == ""


@pytest.mark.django_db
def test_un_sitio_web_invalido_responde_422(client, edicion_publicada, token_admin, media_root):
    """GIVEN un `sitio_web` que no es una URL
    THEN   422 con `field_errors`: el campo del modelo es un `URLField` y
            `Model.save()` NO ejecuta los validadores.
    """
    payload = make_patrocinador_payload(sitio_web="no es una url")

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 422, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "VALIDATION_ERROR"
    assert any(error["field"] == "sitio_web" for error in cuerpo["error"]["field_errors"])
    assert Patrocinador.objects.count() == 0


# ── Permisos y envoltura ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_un_anonimo_recibe_401(client, edicion_publicada, media_root):
    """GIVEN una petición sin token · WHEN se crea el patrocinador
    THEN   401 AUTHENTICATION_REQUIRED: la autenticación precede al permiso.
    """
    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
    )

    assert respuesta.status_code == 401, respuesta.content
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_una_cuenta_normal_recibe_403(
    client, edicion_publicada, media_root, django_user_model
):
    """GIVEN una cuenta autenticada SIN permiso administrativo
    THEN   403 ACTION_NOT_ALLOWED.
    """
    from ninja_jwt.tokens import AccessToken

    from modules.usuarios.domain.models import Usuario

    usuario = Usuario.objects.create_user(
        username="normal.patrocinadores",
        password="Prueba-12345",
        email="normal.patrocinadores@example.com",
    )
    token = AccessToken.for_user(usuario)

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert respuesta.status_code == 403, respuesta.content
    assert respuesta.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_el_error_no_filtra_rutas_ni_internos(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un rechazo de media · WHEN se lee el cuerpo
    THEN   la prosa es la del catálogo: ni rutas, ni nombres de archivo, ni
            texto crudo de excepción.
    """
    token = "file_aaa111"
    payload = make_patrocinador_payload(imagenes=[make_imagen_payload(token)])

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(payload),
            "files": [_parte(token, b"mentira" * 20, "mentira.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    cuerpo = respuesta.json()
    texto = json.dumps(cuerpo)
    assert str(media_root) not in texto
    assert "Traceback" not in texto
    assert "mentira.png" not in texto
    assert "MEDIA_ROOT" not in texto
