"""El recorrido completo de la sala de proyección.

Change: `public-video-streaming-crud`

GIVEN  una galería pública vacía
WHEN   el administrador publica un video, lo edita y lo borra
THEN   la galería pública refleja cada paso y, al final, el video ya no está.
"""

import json

import pytest

from modules.videos.domain.models import Video
from modules.videos.tests.factories import (
    make_video_payload,
    make_video_update_payload,
)


@pytest.mark.django_db
def test_e2e_publicar_editar_y_borrar_un_video(client, token_admin_videos):
    """GIVEN la sala de proyección vacía
    WHEN  el administrador publica, edita y borra un video
    THEN  la galería pública refleja cada paso y el video desaparece al final.
    """
    # 1 · La galería pública empieza vacía.
    respuesta = client.get("/api/videos")
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"] == []

    # 2 · El administrador publica un video.
    respuesta = client.post(
        "/api/administracion/videos",
        data=json.dumps(make_video_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )
    assert respuesta.status_code == 201, respuesta.content
    video_id = respuesta.json()["data"]["id"]

    # 3 · La galería pública ya lo publica.
    respuesta = client.get("/api/videos")
    assert respuesta.status_code == 200, respuesta.content
    galeria = respuesta.json()["data"]
    assert len(galeria) == 1
    assert galeria[0]["id"] == video_id

    # 4 · El detalle público lo devuelve con su contrato.
    respuesta = client.get(f"/api/videos/{video_id}")
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"]["titulo"] == "Presentación del festival"

    # 5 · El administrador lo edita.
    respuesta = client.patch(
        f"/api/administracion/videos/{video_id}",
        data=json.dumps(make_video_update_payload(titulo="Charla inaugural")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"]["titulo"] == "Charla inaugural"

    # 6 · El listado administrativo lo muestra con el filtro.
    respuesta = client.get(
        "/api/administracion/videos?q=charla",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"]["total"] == 1

    # 7 · El administrador lo borra.
    respuesta = client.delete(
        f"/api/administracion/videos/{video_id}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )
    assert respuesta.status_code == 204, respuesta.content

    # 8 · La galería pública vuelve a estar vacía y el detalle responde 404.
    respuesta = client.get("/api/videos")
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"] == []

    respuesta = client.get(f"/api/videos/{video_id}")
    assert respuesta.status_code == 404, respuesta.content
    assert respuesta.json()["error"]["code"] == "VIDEO_NO_ENCONTRADO"
    assert Video.objects.count() == 0
