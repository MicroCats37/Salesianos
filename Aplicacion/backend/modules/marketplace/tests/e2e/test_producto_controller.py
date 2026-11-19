"""Superficie HTTP del catálogo de la tienda (lecturas públicas).

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-MD-1.0.0`

Cubre las rutas de lectura del ledger (FR-07 §3.3):

- `RT-MK-01` GET `/marketplace/categorias`;
- `RT-MK-02` GET `/marketplace/productos` (con la paginación congelada);
- `RT-MK-03` GET `/marketplace/productos/{slug}`.

Y las garantías del catálogo: alcance de edición, orden de la galería,
precio autoritativo y degradación con aviso cuando el archivo falta.
"""

import json

import pytest

from modules.marketplace.domain.models import Producto

pytestmark = pytest.mark.urls("modules.marketplace.tests.urls_marketplace")


@pytest.mark.django_db
def test_las_categorias_son_publicas_y_ordenadas(
    client, edicion_publicada, categoria_producto, media_root
):
    """GIVEN una edición publicada con categorías · WHEN se consulta el catálogo
    THEN   200 sin autenticación y las categorías en orden canónico.
    """
    from modules.marketplace.domain.models import CategoriaProducto

    CategoriaProducto.objects.create(
        edicion=edicion_publicada, nombre="Aperitivos", slug="aperitivos", orden=0
    )

    respuesta = client.get("/api/marketplace/categorias")

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is True
    assert [item["slug"] for item in cuerpo["data"]] == ["aperitivos", "bebidas"]
    assert cuerpo["data"][0]["orden"] == 0


@pytest.mark.django_db
def test_el_catalogo_usa_la_paginacion_congelada(client, edicion_publicada, media_root):
    """GIVEN productos activos e inactivos · WHEN se lista el catálogo
    THEN   la paginación vive DENTRO de `data` y sólo salen los `ACTIVO`.
    """
    Producto.objects.create(
        edicion=edicion_publicada, nombre="Agua", slug="agua", precio="3.50"
    )
    Producto.objects.create(
        edicion=edicion_publicada,
        nombre="Oculto",
        slug="oculto",
        precio="9.00",
        estado="INACTIVO",
    )

    respuesta = client.get("/api/marketplace/productos?page=1&page_size=10")

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert set(datos) == {"items", "total", "page", "page_size", "total_pages"}
    assert datos["total"] == 1
    assert datos["page"] == 1
    assert datos["page_size"] == 10
    assert datos["total_pages"] == 1
    assert [item["slug"] for item in datos["items"]] == ["agua"]
    assert datos["items"][0]["precio_efectivo"] == "3.50"


@pytest.mark.django_db
def test_el_detalle_trae_la_galeria_ordenada(client, edicion_publicada, media_root):
    """GIVEN un producto con dos imágenes · WHEN se pide el detalle
    THEN   la galería viaja ORDENADA y cada imagen dice si su archivo existe.
    """
    from modules.marketplace.domain.models import ProductoImagen

    producto = Producto.objects.create(
        edicion=edicion_publicada, nombre="Agua", slug="agua", precio="3.50"
    )
    ProductoImagen.objects.create(
        producto=producto, imagen="productos/x/segunda.png", orden=1
    )
    ProductoImagen.objects.create(
        producto=producto, imagen="productos/x/primera.png", orden=0
    )

    respuesta = client.get("/api/marketplace/productos/agua")

    assert respuesta.status_code == 200, respuesta.content
    datos = respuesta.json()["data"]
    assert [imagen["orden"] for imagen in datos["imagenes"]] == [0, 1]
    # Los archivos no existen en el volumen: la galería DEGRADA CON AVISO.
    assert [imagen["disponible"] for imagen in datos["imagenes"]] == [False, False]
    assert [imagen["url"] for imagen in datos["imagenes"]] == [None, None]


@pytest.mark.django_db
def test_un_slug_inexistente_responde_404(client, edicion_publicada, media_root):
    """GIVEN un slug que no existe · WHEN se pide el detalle
    THEN   404 con un código estable y SIN filtrar información interna.
    """
    respuesta = client.get("/api/marketplace/productos/no-existe")

    assert respuesta.status_code == 404, respuesta.content
    cuerpo = respuesta.json()
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "PRODUCTO_NO_ENCONTRADO"
    assert "Traceback" not in json.dumps(cuerpo)


@pytest.mark.django_db
def test_sin_edicion_publicada_el_catalogo_responde_404(client, db, media_root):
    """GIVEN ninguna edición publicada · WHEN se consulta el catálogo
    THEN   404 EDICION_NO_RESUELTA: nunca se opera sobre "la edición que haya".
    """
    respuesta = client.get("/api/marketplace/productos")

    assert respuesta.status_code == 404, respuesta.content
    assert respuesta.json()["error"]["code"] == "EDICION_NO_RESUELTA"
