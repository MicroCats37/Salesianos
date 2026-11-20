"""Superficie HTTP de ADMINISTRACIÓN de la sala de proyección (escrituras).

Change: `public-video-streaming-crud`

Cubre las tres verbs de escritura del panel:

- `POST /api/administracion/videos` — publicar;
- `PATCH /api/administracion/videos/{video_id}` — editar;
- `DELETE /api/administracion/videos/{video_id}` — borrar.

Y la garantía de la URL: el servidor SÓLO admite `http` y `https`. Un
`javascript:` o un `ftp:` se rechazan con 422 y NO se persisten.
"""

import json

import pytest

from modules.videos.domain.models import Video
from modules.videos.tests.factories import (
    make_video_payload,
    make_video_update_payload,
)


@pytest.mark.django_db
def test_publicar_un_video_persiste_la_fila(client, token_admin_videos):
    """GIVEN una cuenta administradora · WHEN publica un video
    THEN   201 con la envoltura congelada, un mensaje fijo y la fila persistida.
    """
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["message"] == "El video se registró correctamente."
    assert cuerpo["data"]["titulo"] == "Presentación del festival"

    assert Video.objects.count() == 1
    assert Video.objects.get().url == "https://media.salesianosfest.org/videos/presentacion.mp4"


@pytest.mark.django_db
def test_publicar_un_video_exige_credencial(client):
    """GIVEN sin credencial · WHEN se publica
    THEN   401: nadie publica sin cuenta.
    """
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload()),
        content_type="application/json",
    )

    assert respuesta.status_code == 401, respuesta.content
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_publicar_sin_titulo_responde_422_con_errores_por_campo(client, token_admin_videos):
    """GIVEN un payload sin título · WHEN se publica
    THEN   422 y el error viaja por `error.field_errors`.
    """
    payload = make_video_payload()
    payload.pop("titulo")

    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 422, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    campos = {entrada["field"] for entrada in cuerpo["error"]["field_errors"]}
    assert "titulo" in campos
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_publicar_con_una_url_javascript_responde_422_y_no_persiste(
    client, token_admin_videos
):
    """GIVEN una URL `javascript:` · WHEN se publica
    THEN   422 y NADA se persiste: un esquema ejecutable no es una URL.
    """
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload(url="javascript:alert(1)")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 422, respuesta.content
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_publicar_con_una_url_ftp_responde_422_y_no_persiste(client, token_admin_videos):
    """GIVEN una URL `ftp:` · WHEN se publica
    THEN   422 y NADA se persiste: sólo `http` y `https` son direcciones de
            video.
    """
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload(url="ftp://ejemplo.org/video.mp4")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 422, respuesta.content
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_publicar_con_una_url_data_responde_422_y_no_persiste(client, token_admin_videos):
    """GIVEN una URL `data:` · WHEN se publica
    THEN   422 y NADA se persiste.
    """
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload(url="data:text/html,<h1>hola</h1>")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 422, respuesta.content
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_editar_un_video_solo_cambia_los_campos_enviados(client, video, token_admin_videos):
    """GIVEN un video publicado · WHEN se envía un `PATCH` parcial
    THEN   200 y SÓLO cambia el campo enviado.
    """
    respuesta = client.patch(
        f"/api/administracion/videos/{video.id}",
        data=json.dumps(make_video_update_payload(titulo="Nuevo título")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["message"] == "El video se actualizó correctamente."

    video.refresh_from_db()
    assert video.titulo == "Nuevo título"
    assert video.descripcion == "El saludo de apertura."
    assert video.url == "https://media.salesianosfest.org/videos/presentacion.mp4"


@pytest.mark.django_db
def test_editar_un_video_inexistente_responde_404(client, db, token_admin_videos):
    """GIVEN un identificador que no existe · WHEN se edita
    THEN   404 `VIDEO_NO_ENCONTRADO`.
    """
    import uuid

    respuesta = client.patch(
        f"/api/administracion/videos/{uuid.uuid4()}",
        data=json.dumps(make_video_update_payload(titulo="Nuevo título")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 404, respuesta.content
    assert respuesta.json()["error"]["code"] == "VIDEO_NO_ENCONTRADO"


@pytest.mark.django_db
def test_editar_con_una_url_no_permitida_responde_422_y_no_cambia_nada(
    client, video, token_admin_videos
):
    """GIVEN un video publicado · WHEN se edita con una URL `javascript:`
    THEN   422 y el video SIGUE igual: el rechazo no escribe a medias.
    """
    respuesta = client.patch(
        f"/api/administracion/videos/{video.id}",
        data=json.dumps(make_video_update_payload(url="javascript:alert(1)")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 422, respuesta.content

    video.refresh_from_db()
    assert video.url == "https://media.salesianosfest.org/videos/presentacion.mp4"


@pytest.mark.django_db
def test_borrar_un_video_responde_204_sin_cuerpo(client, video, token_admin_videos):
    """GIVEN un video publicado · WHEN se borra
    THEN   204 SIN CUERPO y la fila desaparece.
    """
    respuesta = client.delete(
        f"/api/administracion/videos/{video.id}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 204, respuesta.content
    assert respuesta.content == b""
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_borrar_dos_veces_el_mismo_video_responde_404(client, video, token_admin_videos):
    """GIVEN un video borrado · WHEN se borra de nuevo
    THEN   404: el borrado NO es idempotente, para que el operador sepa si la
            fila estaba.
    """
    client.delete(
        f"/api/administracion/videos/{video.id}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    respuesta = client.delete(
        f"/api/administracion/videos/{video.id}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 404, respuesta.content
    assert respuesta.json()["error"]["code"] == "VIDEO_NO_ENCONTRADO"


@pytest.mark.django_db
def test_borrar_exige_credencial(client, video):
    """GIVEN sin credencial · WHEN se borra
    THEN   401 y el video sigue published.
    """
    respuesta = client.delete(f"/api/administracion/videos/{video.id}")

    assert respuesta.status_code == 401, respuesta.content
    assert Video.objects.count() == 1
