"""Superficie HTTP PÚBLICA de la sala de proyección.

Change: `public-video-streaming-crud`

Cubre las dos rutas públicas del módulo:

- `GET /api/videos` — la galería;
- `GET /api/videos/{video_id}` — el detalle.

Y las garantías del módulo: la superficie pública NO expone escrituras, la
envoltura es la CONGELADA y un video inexistente responde 404 con un código
estable, sin filtrar información interna.
"""

import json

import pytest

from modules.videos.domain.models import Video


@pytest.mark.django_db
def test_la_galeria_publica_devuelve_la_envoltura_congelada(client, video):
    """GIVEN un video publicado · WHEN se consulta la galería
    THEN   200 con `success`/`data`/`error`/`message` y la lista de videos.
    """
    respuesta = client.get("/api/videos")

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"success", "data", "error", "message"}
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert isinstance(cuerpo["data"], list)
    assert len(cuerpo["data"]) == 1


@pytest.mark.django_db
def test_la_galeria_publica_no_necesita_autenticacion(client, video):
    """GIVEN una galería publicada · WHEN se consulta SIN credencial
    THEN   200: un video es público por definición.
    """
    respuesta = client.get("/api/videos")

    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["success"] is True


@pytest.mark.django_db
def test_cada_video_de_la_galeria_trae_su_contrato(client, video):
    """GIVEN un video · WHEN se consulta la galería
    THEN   cada fila declara `id`, `titulo`, `descripcion`, `url` y
            `created_at`.
    """
    respuesta = client.get("/api/videos")

    assert respuesta.status_code == 200, respuesta.content
    item = respuesta.json()["data"][0]
    assert set(item) == {"id", "titulo", "descripcion", "url", "created_at"}
    assert item["id"] == str(video.id)
    assert item["titulo"] == video.titulo
    assert item["descripcion"] == video.descripcion
    assert item["url"] == video.url


@pytest.mark.django_db
def test_la_galeria_vacia_no_es_un_error(client, db):
    """GIVEN ninguna galería publicada · WHEN se consulta la galería
    THEN   200 con `data == []`: una galería vacía NO es un fallo.
    """
    respuesta = client.get("/api/videos")

    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["data"] == []


@pytest.mark.django_db
def test_la_galeria_ordena_del_mas_reciente_al_mas_antiguo(client, video, video_2):
    """GIVEN dos videos · WHEN se consulta la galería
    THEN   el más reciente va primero (orden canónico `-created_at`).
    """
    respuesta = client.get("/api/videos")

    assert respuesta.status_code == 200, respuesta.content
    titulos = [item["titulo"] for item in respuesta.json()["data"]]
    assert titulos == ["Charla deinners", "Presentación del festival"]


@pytest.mark.django_db
def test_el_detalle_publico_devuelve_el_video(client, video):
    """GIVEN un video · WHEN se pide su detalle
    THEN   200 con el video completo, `created_at` y `updated_at`.
    """
    respuesta = client.get(f"/api/videos/{video.id}")

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["id"] == str(video.id)
    assert datos["titulo"] == video.titulo
    assert datos["url"] == video.url
    assert "created_at" in datos
    assert "updated_at" in datos


@pytest.mark.django_db
def test_un_video_inexistente_responde_404(client, db):
    """GIVEN un identificador que no existe · WHEN se pide el detalle
    THEN   404 con `VIDEO_NO_ENCONTRADO` y SIN filtrar información interna.
    """
    import uuid

    respuesta = client.get(f"/api/videos/{uuid.uuid4()}")

    assert respuesta.status_code == 404, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "VIDEO_NO_ENCONTRADO"
    assert "Traceback" not in json.dumps(cuerpo)


@pytest.mark.django_db
def test_la_superficie_publica_no_expone_escrituras(client, video):
    """GIVEN la superficie pública · WHEN se intenta escribir
    THEN   la ruta no existe: publicar un video es tarea del panel.
    """
    from modules.videos.tests.factories import make_video_payload

    for metodo in ("post", "put", "patch", "delete"):
        respuesta = getattr(client, metodo)(
            "/api/videos",
            data=json.dumps(make_video_payload()),
            content_type="application/json",
        )
        assert respuesta.status_code in (404, 405), (metodo, respuesta.content)


@pytest.mark.django_db
def test_el_modelo_no_declara_mas_que_los_campos_aprobados(db):
    """GIVEN el contrato de datos aprobado
    THEN   el modelo tiene EXACTAMENTE seis columnas: ni `es_publico`, ni
            proveedor, ni categorías, ni FK a la edición, ni bloqueo optimista.
    """
    campos = {campo.name for campo in Video._meta.get_fields()}

    assert campos == {
        "id",
        "created_at",
        "updated_at",
        "titulo",
        "descripcion",
        "url",
    }
