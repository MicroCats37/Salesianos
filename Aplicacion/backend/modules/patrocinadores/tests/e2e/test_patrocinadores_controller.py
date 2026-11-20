"""Superficie HTTP de los patrocinadores (ruta `RT-MD-02`).

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-MD-1.0.0`

Cubre la ruta del ledger (FR-07 §3.3):

- `RT-MD-02` POST `/patrocinadores`.

Y las garantías del módulo: alcance de edición resuelto por el servidor,
envoltura de respuesta congelada, orden de la galería y degradación con aviso
cuando el archivo falta.
"""

import json

import pytest

from modules.patrocinadores.domain.models import Patrocinador, PatrocinadorImagen

pytestmark = pytest.mark.urls("modules.patrocinadores.tests.urls_patrocinadores")


@pytest.mark.django_db
def test_el_alta_usa_la_envoltura_congelada(client, edicion_publicada, token_admin, media_root):
    """GIVEN un administrador · WHEN crea un patrocinador
    THEN   200 con `success`/`data`/`error`/`message` y los datos del
            patrocinador.
    """
    from modules.patrocinadores.tests.factories import make_patrocinador_payload

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"success", "data", "error", "message"}
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["message"] is None
    assert cuerpo["data"]["edicion_id"] == str(edicion_publicada.id)
    assert cuerpo["data"]["edicion_nombre"] == edicion_publicada.nombre


@pytest.mark.django_db
def test_el_alta_registra_la_galeria_en_orden(client, edicion_publicada, token_admin, media_root):
    """GIVEN un patrocinador con logo y dos imágenes · WHEN se crea
    THEN   la galería persiste ORDENADA y el logo viaja con su URL.
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    from modules.patrocinadores.tests.factories import (
        make_imagen_payload,
        make_patrocinador_payload,
    )
    from modules.patrocinadores.tests.fixtures.patrocinadores_fixtures import PNG_MINIMO

    token_logo = "file_logo111"
    token_a = "file_aaa111"
    token_b = "file_bbb222"

    def _parte(token: str, nombre: str):
        return SimpleUploadedFile(
            f"{token}___{nombre}", PNG_MINIMO, content_type="image/png"
        )

    respuesta = client.post(
        "/api/patrocinadores",
        data={
            "data": json.dumps(
                make_patrocinador_payload(
                    logo=token_logo,
                    imagenes=[
                        make_imagen_payload(token_a, texto_alternativo="Uno"),
                        make_imagen_payload(token_b, texto_alternativo="Dos"),
                    ],
                )
            ),
            "files": [
                _parte(token_logo, "logo.png"),
                _parte(token_a, "uno.png"),
                _parte(token_b, "dos.png"),
            ],
        },
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert datos["logo"]["url"]
    assert datos["logo"]["disponible"] is True
    assert [imagen["orden"] for imagen in datos["imagenes"]] == [0, 1]
    assert [imagen["texto_alternativo"] for imagen in datos["imagenes"]] == ["Uno", "Dos"]

    patrocinador = Patrocinador.objects.get(slug="colegio-san-juan-bosco")
    assert [imagen.orden for imagen in patrocinador.imagenes.all()] == [0, 1]


@pytest.mark.django_db
def test_el_detalle_de_la_galeria_degrada_sin_fichero(
    client, edicion_publicada, patrocinador, media_root
):
    """GIVEN un patrocinador con una imagen SIN archivo en el volumen
    THEN   la imagen viaja con `disponible = False` y `url = None`.
    """
    PatrocinadorImagen.objects.create(
        patrocinador=patrocinador, imagen="patrocinadores/x/ausente.png", orden=0
    )

    # El módulo NO expone todavía una ruta de lectura por HTTP (el ledger no
    # la declara): la degradación se comprueba sobre el RESULT del dominio,
    # que es lo que consumirá el presenter cuando A0 registre la ruta.
    from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
        PatrocinadorCoreService,
    )

    resultado = PatrocinadorCoreService().result_de(patrocinador)
    assert resultado.imagenes[0].disponible is False
    assert resultado.imagenes[0].url is None


@pytest.mark.django_db
def test_un_slug_duplicado_responde_409(client, edicion_publicada, token_admin, media_root):
    """GIVEN un patrocinador que ya existe con ese slug
    THEN   409 PATROCINADOR_SLUG_DUPLICADO con un código estable.
    """
    from modules.patrocinadores.tests.factories import make_patrocinador_payload

    respuesta = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )
    assert respuesta.status_code == 200, respuesta.content

    repetido = client.post(
        "/api/patrocinadores",
        data=json.dumps(make_patrocinador_payload()),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_admin}",
    )

    assert repetido.status_code == 409, repetido.content
    cuerpo = repetido.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "PATROCINADOR_SLUG_DUPLICADO"
    assert Patrocinador.objects.count() == 1
    assert "Traceback" not in json.dumps(cuerpo)
