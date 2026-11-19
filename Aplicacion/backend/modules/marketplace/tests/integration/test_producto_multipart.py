"""Protocolo multipart de media del marketplace: éxito y fallos.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`

Cubre el protocolo COMPLETO (FR-06 §2.4) sobre la ruta `RT-MD-01`:

- alta JSON (sin imágenes) y alta multipart (con galería ordenada);
- token ausente (`MEDIA_TOKEN_NO_RESUELTO`);
- archivo huérfano (`MEDIA_ARCHIVO_HUERFANO`);
- token duplicado (`MEDIA_TOKEN_DUPLICADO`);
- firma de contenido inválida (`MEDIA_TIPO_NO_PERMITIDO`);
- tamaño excedido (`MEDIA_TAMANO_EXCEDIDO`);
- NINGÚN residuo en el volumen de media tras un rechazo;
- el permiso `Administrador` y la envoltura de respuesta congelada.

Sobre el dinero en el cable: el envelope de `core/responses.py` serializa
los `Decimal` como CADENA decimal (`"3.50"`), porque `model_dump(mode="json")`
de Pydantic v2 los convierte en texto antes de que `_decimal_to_float` pueda
actuar. Es el comportamiento OBSERVABLE y CONGELADO del backend objetivo
(todos los módulos con dinero se comportan así) y por eso el espejo Zod de A7
tiene que reflejarlo. La petición a A0 para explicitar la intención está
registrada en el evidence de DOM-04 (A0-05).
"""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.marketplace.domain.models import Producto
from modules.marketplace.tests.factories import make_imagen_payload, make_producto_payload
from modules.marketplace.tests.fixtures.marketplace_fixtures import (
    JPEG_MINIMO,
    PNG_MINIMO,
)

pytestmark = pytest.mark.urls("modules.marketplace.tests.urls_marketplace")


def _parte(token: str, contenido: bytes, nombre: str, content_type: str):
    """Una parte `files` con el nombre `<token>___<realname>`."""
    return SimpleUploadedFile(
        f"{token}___{nombre}",
        contenido,
        content_type=content_type,
    )


def _multipart(token: str, contenido: bytes, nombre: str, content_type: str):
    return _parte(token, contenido, nombre, content_type)


# ── Éxito ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_alta_json_sin_imagenes(client, edicion_publicada, token_admin, media_root):
    """GIVEN un payload JSON sin archivos · WHEN se crea el producto
    THEN   200 con la envoltura congelada y el producto persistido.
    """
    respuesta = client.post(
        "/api/marketplace/productos",
        data=json.dumps(make_producto_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["nombre"] == "Agua mineral"
    assert cuerpo["data"]["slug"] == "agua-mineral"
    assert cuerpo["data"]["precio"] == "3.50"
    assert cuerpo["data"]["precio_efectivo"] == "3.50"
    assert cuerpo["data"]["oferta_activa"] is False
    assert cuerpo["data"]["imagenes"] == []
    assert Producto.objects.filter(slug="agua-mineral").count() == 1


@pytest.mark.django_db
def test_alta_multipart_guarda_la_galeria_en_orden(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN dos archivos con sus tokens · WHEN se crea el producto
    THEN   la galería persiste ORDENADA y los archivos quedan en el volumen.
    """
    token_a = "file_aaa111"
    token_b = "file_bbb222"
    payload = make_producto_payload(
        imagenes=[
            make_imagen_payload(token_a, es_principal=True, texto_alternativo="Frente"),
            make_imagen_payload(token_b, texto_alternativo="Fondo"),
        ]
    )

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [
                _multipart(token_a, PNG_MINIMO, "uno.png", "image/png"),
                _multipart(token_b, JPEG_MINIMO, "dos.jpg", "image/jpeg"),
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    imagenes = respuesta.json()["data"]["imagenes"]
    assert [imagen["orden"] for imagen in imagenes] == [0, 1]
    assert imagenes[0]["texto_alternativo"] == "Frente"
    assert imagenes[0]["es_principal"] is True
    assert imagenes[1]["es_principal"] is False
    assert all(imagen["url"] for imagen in imagenes)
    assert all(imagen["disponible"] for imagen in imagenes)

    producto = Producto.objects.get(slug="agua-mineral")
    assert producto.imagenes.count() == 2
    assert [imagen.orden for imagen in producto.imagenes.all()] == [0, 1]

    # La ruta es `productos/<producto_id>/<uuid><ext>` (FR-06 §2.2).
    for imagen in producto.imagenes.all():
        assert imagen.imagen.name.startswith(f"productos/{producto.id}/")
        assert imagen.imagen.name.endswith(".png") or imagen.imagen.name.endswith(".jpg")


# ── Rechazos del protocolo ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_token_sin_archivo_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN un token en el payload SIN parte de archivo
    THEN   400 MEDIA_TOKEN_NO_RESUELTO y ningún archivo en el volumen.
    """
    payload = make_producto_payload(imagenes=[make_imagen_payload("file_aaa111")])

    respuesta = client.post(
        "/api/marketplace/productos",
        data={"data": json.dumps(payload)},
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "MEDIA_TOKEN_NO_RESUELTO"
    assert Producto.objects.count() == 0
    assert list(media_root.rglob("*")) == []


@pytest.mark.django_db
def test_archivo_huerfano_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN una parte de archivo que el payload NO referencia
    THEN   400 MEDIA_ARCHIVO_HUERFANO y ningún residuo en el volumen.
    """
    payload = make_producto_payload()

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [_multipart("file_huerfano", PNG_MINIMO, "huerfano.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_ARCHIVO_HUERFANO"
    assert Producto.objects.count() == 0
    assert list(media_root.rglob("*")) == []


@pytest.mark.django_db
def test_token_duplicado_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN el MISMO token dos veces en el payload
    THEN   400 MEDIA_TOKEN_DUPLICADO: el matching es exactamente una vez.
    """
    token = "file_aaa111"
    payload = make_producto_payload(
        imagenes=[make_imagen_payload(token), make_imagen_payload(token)]
    )

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [_multipart(token, PNG_MINIMO, "uno.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TOKEN_DUPLICADO"
    assert Producto.objects.count() == 0
    assert list(media_root.rglob("*")) == []


@pytest.mark.django_db
def test_firma_de_contenido_invalida_se_rechaza(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un archivo que DECLARA `image/png` pero no tiene firma de imagen
    THEN   400 MEDIA_TIPO_NO_PERMITIDO y ningún residuo.
    """
    token = "file_aaa111"
    payload = make_producto_payload(imagenes=[make_imagen_payload(token)])

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [
                _multipart(token, b"esto no es una imagen" * 10, "mentira.png", "image/png")
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 400, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TIPO_NO_PERMITIDO"
    assert Producto.objects.count() == 0
    assert list(media_root.rglob("*")) == []


@pytest.mark.django_db
def test_tamano_excedido_se_rechaza(client, edicion_publicada, token_admin, media_root):
    """GIVEN un archivo que excede el tope de tamaño
    THEN   413 MEDIA_TAMANO_EXCEDIDO y ningún residuo.
    """
    token = "file_aaa111"
    payload = make_producto_payload(imagenes=[make_imagen_payload(token)])
    grande = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 1024)

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [_multipart(token, grande, "grande.png", "image/png")],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 413, respuesta.content
    assert respuesta.json()["error"]["code"] == "MEDIA_TAMANO_EXCEDIDO"
    assert Producto.objects.count() == 0
    assert list(media_root.rglob("*")) == []


@pytest.mark.django_db
def test_payload_invalido_responde_422_con_field_errors(
    client, edicion_publicada, token_admin, media_root
):
    """GIVEN un payload que no valida contra el schema
    THEN   422 con `field_errors` y ningún producto creado.
    """
    payload = make_producto_payload(precio="-1")

    respuesta = client.post(
        "/api/marketplace/productos",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 422, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "VALIDATION_ERROR"
    assert any(error["field"] == "precio" for error in cuerpo["error"]["field_errors"])
    assert Producto.objects.count() == 0


# ── Permisos y envoltura ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_un_anonimo_recibe_401(client, edicion_publicada, media_root):
    """GIVEN una petición sin token · WHEN se crea el producto
    THEN   401 AUTHENTICATION_REQUIRED: la autenticación precede al permiso.
    """
    respuesta = client.post(
        "/api/marketplace/productos",
        data=json.dumps(make_producto_payload()),
        content_type="application/json",
    )

    assert respuesta.status_code == 401, respuesta.content
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_un_cuenta_normal_recibe_403(client, edicion_publicada, media_root, django_user_model):
    """GIVEN una cuenta autenticada SIN permiso administrativo
    THEN   403 ACTION_NOT_ALLOWED.
    """
    from ninja_jwt.tokens import AccessToken

    from modules.usuarios.domain.models import Usuario

    usuario = Usuario.objects.create_user(
        username="normal.tienda",
        password="Prueba-12345",
        email="normal.tienda@example.com",
    )
    token = AccessToken.for_user(usuario)

    respuesta = client.post(
        "/api/marketplace/productos",
        data=json.dumps(make_producto_payload()),
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
    payload = make_producto_payload(imagenes=[make_imagen_payload(token)])

    respuesta = client.post(
        "/api/marketplace/productos",
        data={
            "data": json.dumps(payload),
            "files": [_multipart(token, b"mentira" * 20, "mentira.png", "image/png")],
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
