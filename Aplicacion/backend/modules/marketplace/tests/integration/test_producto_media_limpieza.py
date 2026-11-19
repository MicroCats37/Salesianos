"""Limpieza de media del marketplace: rollback, reemplazo y borrado.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`

Cubre los TRES caminos obligatorios de limpieza de FR-06 §2.5:

- **rollback**: si la operación falla DESPUÉS de escribir un archivo, el
  archivo se borra (la base de datos se revierte sola; el volumen de media no);
- **reemplazo**: el archivo anterior se borra DESPUÉS de que el nuevo quedó
  persistido; si el reemplazo falla, el anterior sigue en su sitio;
- **borrado**: al borrar una imagen o un producto, sus archivos se borran.

Y las reglas de coherencia del catálogo: edición coherente, precio y oferta
autoritativos, módulo lógico deshabilitado.
"""

import pytest
from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.marketplace.domain.constants import EstadoProducto
from modules.marketplace.domain.exceptions import (
    ModuloNoHabilitadoError,
    ProductoCategoriaIncoherenteError,
)
from modules.marketplace.domain.models import Producto, ProductoImagen
from modules.marketplace.domain.schemas.producto_schemas import (
    ImagenProductoData,
    ImagenProductoUploadData,
    ProductoCreateData,
)
from modules.marketplace.domain.services.core.producto_core_service import (
    ProductoCoreService,
)
from modules.marketplace.domain.services.core.producto_media_service import (
    ProductoMediaService,
)
from modules.marketplace.domain.services.flujos.producto_flujo import ProductoFlujo
from modules.marketplace.tests.fixtures.marketplace_fixtures import PNG_MINIMO


# ── Dobles de test ──────────────────────────────────────────────────────────


class MediaServiceQueFalla(ProductoMediaService):
    """Doble que falla al escribir la SEGUNDA imagen.

    Permite ejercitar el rollback de media: el primer archivo YA se escribió
    en disco y la operación falla después.
    """

    def __init__(self, falla_en: int = 2):
        self.falla_en = falla_en
        self.escrituras = 0

    def escribir(self, producto, imagen, orden, rutas_escritas):
        self.escrituras += 1
        if self.escrituras == self.falla_en:
            raise RuntimeError("fallo simulado al escribir la imagen")
        return super().escribir(producto, imagen, orden, rutas_escritas)


def _upload(token: str = "file_aaa111") -> ImagenProductoUploadData:
    """Un archivo de imagen YA validado (lo que hace el borde HTTP)."""
    return ImagenProductoUploadData(
        token=token,
        archivo=SimpleUploadedFile("imagen.png", PNG_MINIMO, content_type="image/png"),
        mime_detectado="image/png",
        extension=".png",
        tamano=len(PNG_MINIMO),
        nombre_original="imagen.png",
    )


def _imagen(token: str = "file_aaa111", **extra) -> ImagenProductoData:
    return ImagenProductoData(token=token, upload=_upload(token), **extra)


def _alta(edicion_id, imagenes=None, **extra) -> ProductoCreateData:
    payload = {
        "edicion_id": edicion_id,
        "nombre": "Agua mineral",
        "slug": "agua-mineral",
        "descripcion": "Botella de 500 ml.",
        "precio": "3.50",
        "estado": EstadoProducto.ACTIVO,
    }
    payload.update(extra)
    return ProductoCreateData(imagenes=imagenes or [], **payload)


# ── Rollback ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_un_rollback_deja_el_volumen_sin_residuos(edicion_publicada, media_root):
    """GIVEN un fallo DESPUÉS de escribir el primer archivo
    THEN   el archivo se borra, la fila no existe y el volumen queda vacío.
    """
    media = MediaServiceQueFalla(falla_en=2)
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=media)

    with pytest.raises(RuntimeError):
        async_to_sync(flujo.crear_producto)(
            _alta(edicion_publicada.id, imagenes=[_imagen(), _imagen("file_bbb222")])
        )

    assert Producto.objects.count() == 0
    assert ProductoImagen.objects.count() == 0
    assert [ruta for ruta in media_root.rglob("*") if ruta.is_file()] == []


@pytest.mark.django_db
def test_una_alta_exitosa_persiste_los_archivos(edicion_publicada, media_root):
    """GIVEN un alta sin fallos · WHEN se crea el producto
    THEN   los archivos quedan en el volumen, en la ruta congelada.
    """
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())

    async_to_sync(flujo.crear_producto)(_alta(edicion_publicada.id, imagenes=[_imagen()]))

    producto = Producto.objects.get(slug="agua-mineral")
    imagen = producto.imagenes.first()
    assert imagen is not None
    assert (media_root / imagen.imagen.name).exists()
    assert imagen.imagen.name.startswith(f"productos/{producto.id}/")


# ── Reemplazo ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_reemplazar_borra_el_archivo_anterior_despues_del_nuevo(
    edicion_publicada, media_root
):
    """GIVEN una imagen persistida · WHEN se reemplaza su archivo
    THEN   el archivo nuevo existe, el anterior se borró y la fila conserva
            su identificador y su orden.
    """
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())
    async_to_sync(flujo.crear_producto)(_alta(edicion_publicada.id, imagenes=[_imagen()]))

    producto = Producto.objects.get(slug="agua-mineral")
    imagen = producto.imagenes.first()
    ruta_previa = imagen.imagen.name
    assert (media_root / ruta_previa).exists()

    async_to_sync(flujo.reemplazar_imagen)(producto.id, imagen.id, _upload("file_nueva"))

    imagen.refresh_from_db()
    assert imagen.imagen.name != ruta_previa
    assert (media_root / imagen.imagen.name).exists()
    assert not (media_root / ruta_previa).exists()
    assert imagen.orden == 0
    assert ProductoImagen.objects.count() == 1


@pytest.mark.django_db
def test_un_reemplazo_fallido_conserva_el_archivo_anterior(
    edicion_publicada, media_root
):
    """GIVEN un reemplazo que falla · THEN el archivo anterior sigue en su
    sitio y no queda ningún archivo nuevo.
    """
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())
    async_to_sync(flujo.crear_producto)(_alta(edicion_publicada.id, imagenes=[_imagen()]))

    producto = Producto.objects.get(slug="agua-mineral")
    imagen = producto.imagenes.first()
    ruta_previa = imagen.imagen.name

    class MediaQueFalla(ProductoMediaService):
        def reemplazar(self, producto, imagen_previa, upload, rutas_escritas):
            raise RuntimeError("fallo simulado al reemplazar")

    flujo_fallido = ProductoFlujo(
        core_service=ProductoCoreService(), media_service=MediaQueFalla()
    )
    with pytest.raises(RuntimeError):
        async_to_sync(flujo_fallido.reemplazar_imagen)(
            producto.id, imagen.id, _upload("file_nueva")
        )

    imagen.refresh_from_db()
    assert imagen.imagen.name == ruta_previa
    assert (media_root / ruta_previa).exists()
    assert len(list(media_root.rglob("*.png"))) == 1


# ── Borrado ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_borrar_una_imagen_borra_su_archivo(edicion_publicada, media_root):
    """GIVEN un producto con una imagen · WHEN se borra la imagen
    THEN   la fila desaparece y el archivo también.
    """
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())
    async_to_sync(flujo.crear_producto)(_alta(edicion_publicada.id, imagenes=[_imagen()]))

    producto = Producto.objects.get(slug="agua-mineral")
    imagen = producto.imagenes.first()
    ruta = imagen.imagen.name
    assert (media_root / ruta).exists()

    async_to_sync(flujo.eliminar_imagen)(producto.id, imagen.id)

    assert ProductoImagen.objects.count() == 0
    assert not (media_root / ruta).exists()


@pytest.mark.django_db
def test_borrar_un_producto_borra_todos_sus_archivos(edicion_publicada, media_root):
    """GIVEN un producto con dos imágenes · WHEN se borra el producto
    THEN   ni la fila ni los archivos quedan en el volumen.
    """
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())
    async_to_sync(flujo.crear_producto)(
        _alta(edicion_publicada.id, imagenes=[_imagen(), _imagen("file_bbb222")])
    )

    producto = Producto.objects.get(slug="agua-mineral")
    rutas = [imagen.imagen.name for imagen in producto.imagenes.all()]
    assert len(rutas) == 2

    async_to_sync(flujo.eliminar_producto)(producto.id)

    assert Producto.objects.count() == 0
    for ruta in rutas:
        assert not (media_root / ruta).exists()
    assert [ruta for ruta in media_root.rglob("*") if ruta.is_file()] == []


# ── Coherencia y autoridad del dominio ──────────────────────────────────────


@pytest.mark.django_db
def test_una_categoria_de_otra_edicion_se_rechaza(edicion_publicada, edicion_otra, media_root):
    """GIVEN una categoría de OTRA edición · WHEN se crea el producto
    THEN   se rechaza: producto y categoría viven en el mismo alcance.
    """
    from modules.marketplace.domain.models import CategoriaProducto

    categoria_ajena = CategoriaProducto.objects.create(
        edicion=edicion_otra,
        nombre="Merienda",
        slug="merienda",
        orden=1,
    )
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())

    with pytest.raises(ProductoCategoriaIncoherenteError):
        async_to_sync(flujo.crear_producto)(
            _alta(edicion_publicada.id, categoria_id=categoria_ajena.id)
        )

    assert Producto.objects.count() == 0


@pytest.mark.django_db
def test_el_precio_efectivo_lo_decide_el_dominio(edicion_publicada, media_root):
    """GIVEN un producto con oferta vigente y otro con la oferta caducada
    THEN   el precio efectivo es el de oferta en el primero y el normal en
            el segundo: el cliente NUNCA lo calcula.
    """
    from datetime import timedelta

    from django.utils import timezone

    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())

    ahora = timezone.now()
    async_to_sync(flujo.crear_producto)(
        _alta(
            edicion_publicada.id,
            slug="agua-vigente",
            precio="10.00",
            precio_oferta="7.00",
            oferta_inicia=ahora - timedelta(days=1),
            oferta_termina=ahora + timedelta(days=1),
        )
    )
    async_to_sync(flujo.crear_producto)(
        _alta(
            edicion_publicada.id,
            slug="agua-caducada",
            precio="10.00",
            precio_oferta="7.00",
            oferta_inicia=ahora - timedelta(days=10),
            oferta_termina=ahora - timedelta(days=1),
        )
    )

    vigente = Producto.objects.get(slug="agua-vigente")
    caducada = Producto.objects.get(slug="agua-caducada")
    assert vigente.oferta_activa() is True
    assert vigente.precio_efectivo() == vigente.precio_oferta
    assert caducada.oferta_activa() is False
    assert caducada.precio_efectivo() == caducada.precio


@pytest.mark.django_db
def test_una_ventana_de_oferta_invertida_se_rechaza(edicion_publicada, media_root):
    """GIVEN una oferta cuyo fin precede a su inicio
    THEN   se rechaza con OFERTA_INVALIDA: es incoherencia estructural.
    """
    from datetime import timedelta

    from django.utils import timezone

    from modules.marketplace.domain.exceptions import OfertaInvalidaError

    ahora = timezone.now()
    flujo = ProductoFlujo(core_service=ProductoCoreService(), media_service=ProductoMediaService())

    with pytest.raises(OfertaInvalidaError):
        async_to_sync(flujo.crear_producto)(
            _alta(
                edicion_publicada.id,
                precio="10.00",
                precio_oferta="7.00",
                oferta_inicia=ahora,
                oferta_termina=ahora - timedelta(days=1),
            )
        )

    assert Producto.objects.count() == 0


@pytest.mark.django_db
def test_el_result_expone_el_precio_efectivo(edicion_publicada, media_root):
    """GIVEN un producto con oferta · WHEN se proyecta al result
    THEN   el result lleva `precio_efectivo` y `oferta_activa` calculados.
    """
    from datetime import timedelta

    from django.utils import timezone

    core = ProductoCoreService()
    flujo = ProductoFlujo(core_service=core, media_service=ProductoMediaService())

    ahora = timezone.now()
    async_to_sync(flujo.crear_producto)(
        _alta(
            edicion_publicada.id,
            precio="10.00",
            precio_oferta="7.00",
            oferta_inicia=ahora - timedelta(days=1),
            oferta_termina=ahora + timedelta(days=1),
        )
    )

    producto = Producto.objects.get(slug="agua-mineral")
    result = core.result_de(producto)
    assert result.oferta_activa is True
    assert result.precio_efectivo == producto.precio_oferta
    assert result.precio == producto.precio


@pytest.mark.django_db
def test_el_modulo_deshabilitado_no_expone_catalogo(edicion_sin_marketplace, media_root):
    """GIVEN una edición con el módulo `marketplace` DESHABILITADO
    THEN   la operación se rechaza con MODULO_NO_HABILITADO (RN-E02).
    """
    from modules.marketplace.domain.services.orchestrators.producto_orchestrator import (
        ProductoOrchestrator,
    )
    from modules.marketplace.infrastructure.services.alcance_edicion_eventos import (
        AlcanceEdicionEventos,
    )

    orquestador = ProductoOrchestrator(
        core_service=ProductoCoreService(),
        flujo=ProductoFlujo(
            core_service=ProductoCoreService(), media_service=ProductoMediaService()
        ),
        alcance=AlcanceEdicionEventos(),
    )

    with pytest.raises(ModuloNoHabilitadoError):
        async_to_sync(orquestador.listar_categorias)()
