"""Superficie HTTP de ADMINISTRACIÓN de la sala de proyección (lecturas).

Change: `public-video-streaming-crud`

Cubre la frontera de permisos y las lecturas del panel:

- `GET /api/administracion/videos` — el listado paginado;
- `GET /api/administracion/videos/{video_id}` — el detalle.

Y la garantía de la frontera: **401 ANTES que 403**. Un anónimo recibe 401
y nunca llega a la comprobación de autorización.
"""

import json

import pytest


@pytest.mark.django_db
def test_un_anonimo_recibe_401_en_el_listado(client, video):
    """GIVEN una galería publicada · WHEN se lista SIN credencial
    THEN   401 `AUTHENTICATION_REQUIRED`: la autenticación va antes que la
            autorización.
    """
    respuesta = client.get("/api/administracion/videos")

    assert respuesta.status_code == 401, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_una_cuenta_normal_recibe_403_en_el_listado(client, video, token_no_admin_videos):
    """GIVEN una cuenta autenticada que NO es staff · WHEN se lista
    THEN   403 `ACTION_NOT_ALLOWED`.
    """
    respuesta = client.get(
        "/api/administracion/videos",
        HTTP_AUTHORIZATION=f"Bearer {token_no_admin_videos}",
    )

    assert respuesta.status_code == 403, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert "Traceback" not in json.dumps(cuerpo)


@pytest.mark.django_db
def test_el_listado_administrativo_usa_la_paginacion_congelada(
    client, video, video_2, token_admin_videos
):
    """GIVEN una cuenta administradora · WHEN se lista
    THEN   la paginación vive DENTRO de `data` con la forma congelada.
    """
    respuesta = client.get(
        "/api/administracion/videos?page=1&page_size=1",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert set(datos) == {"items", "total", "page", "page_size", "total_pages"}
    assert datos["total"] == 2
    assert datos["page"] == 1
    assert datos["page_size"] == 1
    assert datos["total_pages"] == 2
    assert len(datos["items"]) == 1


@pytest.mark.django_db
def test_el_listado_administrativo_filtra_por_texto(client, video, video_2, token_admin_videos):
    """GIVEN dos videos · WHEN se busca por el título de uno
    THEN   el filtro viaja al SERVIDOR y sólo sale el video que coincide.
    """
    respuesta = client.get(
        "/api/administracion/videos?q=charla",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["total"] == 1
    assert datos["items"][0]["titulo"] == "Charla deinners"


@pytest.mark.django_db
def test_el_detalle_administrativo_devuelve_el_video(client, video, token_admin_videos):
    """GIVEN una cuenta administradora · WHEN se pide el detalle
    THEN   200 con el video completo.
    """
    respuesta = client.get(
        f"/api/administracion/videos/{video.id}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["id"] == str(video.id)
    assert datos["titulo"] == video.titulo
    assert "updated_at" in datos


@pytest.mark.django_db
def test_el_detalle_administrativo_de_un_video_inexistente_responde_404(
    client, db, token_admin_videos
):
    """GIVEN un identificador que no existe · WHEN se pide el detalle
    THEN   404 `VIDEO_NO_ENCONTRADO`.
    """
    import uuid

    respuesta = client.get(
        f"/api/administracion/videos/{uuid.uuid4()}",
        HTTP_AUTHORIZATION=f"Bearer {token_admin_videos}",
    )

    assert respuesta.status_code == 404, respuesta.content
    assert respuesta.json()["error"]["code"] == "VIDEO_NO_ENCONTRADO"


@pytest.mark.django_db
def test_el_detalle_administrativo_exige_credencial(client, video):
    """GIVEN un video · WHEN se pide el detalle SIN credencial
    THEN   401: la gestión no se abre a un anónimo.
    """
    respuesta = client.get(f"/api/administracion/videos/{video.id}")

    assert respuesta.status_code == 401, respuesta.content
    assert respuesta.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
