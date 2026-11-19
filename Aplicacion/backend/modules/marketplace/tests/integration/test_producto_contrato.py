"""Contrato de datos del catálogo de productos.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md` ·
          `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

GIVEN  el paquete `modules.marketplace`
WHEN   se comprueba su contrato congelado
THEN   la versión de schema coincide con el registro de A0, el modelo tiene
       los campos del contrato de datos mínimo, los DATABASES son las
       autoridades de unicidad y la representación de un archivo es ÚNICA.
"""

from pathlib import Path

import pytest
from django.db import IntegrityError, transaction

from core.contract_versions import SCHEMA_VERSIONS, hay_drift
from modules.marketplace.domain.models import (
    CategoriaProducto,
    Producto,
    ProductoImagen,
)
from modules.marketplace.presentation.schemas import SCHEMA_VERSION

#: Raíz del paquete `modules.marketplace`.
RAIZ_PAQUETE = Path(__file__).resolve().parent.parent.parent


def test_la_version_de_schema_coincide_con_el_registro_de_a0():
    """FR-07 §1.1: la versión del módulo vive en `presentation/schemas/`."""
    assert SCHEMA_VERSION == SCHEMA_VERSIONS["marketplace"]
    assert not hay_drift(SCHEMA_VERSION, SCHEMA_VERSIONS["marketplace"])


@pytest.mark.django_db
def test_el_contrato_de_datos_minimo_esta_completo(db):
    """FR-06 §2.6 y el plan `funcional/03` §1: los campos congelados."""
    campos_producto = {campo.name for campo in Producto._meta.get_fields()}
    for requerido in (
        "id",
        "edicion",
        "categoria",
        "nombre",
        "slug",
        "descripcion",
        "precio",
        "precio_oferta",
        "oferta_inicia",
        "oferta_termina",
        "estado",
        "created_at",
        "updated_at",
    ):
        assert requerido in campos_producto, requerido

    campos_imagen = {campo.name for campo in ProductoImagen._meta.get_fields()}
    for requerido in ("id", "producto", "imagen", "orden", "es_principal"):
        assert requerido in campos_imagen, requerido

    campos_categoria = {campo.name for campo in CategoriaProducto._meta.get_fields()}
    for requerido in ("id", "edicion", "nombre", "slug", "orden"):
        assert requerido in campos_categoria, requerido


@pytest.mark.django_db
def test_el_slug_del_producto_es_unico_por_edicion(edicion_publicada, edicion_otra):
    """GIVEN dos productos con el mismo slug en ediciones DISTINTAS
    THEN   ambos existen: la unicidad es POR EDICIÓN, no global.
    """
    Producto.objects.create(
        edicion=edicion_publicada, nombre="Agua", slug="agua", precio="3.50"
    )
    Producto.objects.create(edicion=edicion_otra, nombre="Agua", slug="agua", precio="3.50")
    assert Producto.objects.filter(slug="agua").count() == 2


@pytest.mark.django_db
def test_el_slug_del_producto_es_unico_dentro_de_la_edicion(edicion_publicada):
    """GIVEN dos productos con el mismo slug en la MISMA edición
    THEN   la base de datos lo rechaza: la base es la autoridad.
    """
    Producto.objects.create(
        edicion=edicion_publicada, nombre="Agua", slug="agua", precio="3.50"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Producto.objects.create(
                edicion=edicion_publicada, nombre="Agua 2", slug="agua", precio="4.00"
            )


@pytest.mark.django_db
def test_solo_hay_una_imagen_principal_por_producto(producto):
    """GIVEN dos imágenes principales del mismo producto
    THEN   la `UniqueConstraint` condicional lo rechaza (FR-06 §2.6).
    """
    ProductoImagen.objects.create(
        producto=producto, imagen="productos/x/a.png", orden=0, es_principal=True
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProductoImagen.objects.create(
                producto=producto,
                imagen="productos/x/b.png",
                orden=1,
                es_principal=True,
            )


@pytest.mark.django_db
def test_el_orden_de_la_galeria_es_orden_por_id(producto):
    """FR-06 §2.6: el orden canónico es `orden ASC, id ASC`."""
    primera = ProductoImagen.objects.create(
        producto=producto, imagen="productos/x/a.png", orden=5
    )
    segunda = ProductoImagen.objects.create(
        producto=producto, imagen="productos/x/b.png", orden=1
    )
    assert list(producto.imagenes.all()) == [segunda, primera]


def test_la_representacion_de_un_archivo_es_unica():
    """El archivo viaja como `ImagenProductoUploadData` en el DTO.

    El contrato exige UNA sola representación del archivo entre el
    controller, el DTO, el orquestador y el flujo: no hay un segundo
    argumento de archivos en ninguna firma.
    """
    from modules.marketplace.domain.schemas.producto_schemas import (
        ImagenProductoData,
        ImagenProductoUploadData,
        ProductoCreateData,
    )

    assert ImagenProductoUploadData.model_fields["archivo"].annotation is not None
    assert ImagenProductoData.model_fields["upload"].annotation is not None
    assert ProductoCreateData.model_fields["imagenes"].annotation is not None

    firmas = []
    for modulo in (
        "modules.marketplace.presentation.controllers.producto_controller",
        "modules.marketplace.domain.services.flujos.producto_flujo",
    ):
        import importlib

        fuente = Path(importlib.import_module(modulo).__file__).read_text(encoding="utf-8")
        firmas.append(fuente)
    assert "files: list" not in firmas[0]
    assert "archivos: list" not in firmas[1]


def test_el_paquete_no_declara_un_almacenamiento_propio():
    """El almacenamiento es el de `core/media.py`: un solo contrato.

    El módulo NO lee `django.conf.settings` por su cuenta: la política de
    media vive en `core/media.py` (A0) y el módulo la CONSUME.
    """
    from core.media import allowed_domains

    assert "productos" in allowed_domains()

    import importlib

    fuente = Path(
        importlib.import_module(
            "modules.marketplace.domain.services.core.producto_media_service"
        ).__file__
    ).read_text(encoding="utf-8")
    # La ÚNICA escritura de disco es la del storage de Django, a través de
    # la ruta que construye `core.media.construir_ruta_media`.
    assert "construir_ruta_media" in fuente
    assert "from django.conf import settings" not in fuente
