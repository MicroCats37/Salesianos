"""Servicio de media del marketplace: escritura y limpieza de archivos.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`
Contract: `contract/django-app-architecture-contract.md` §4.3 (core services)

Este servicio CONSUME el contrato único de media (`core/media.py`); no
reimplementa allowlist, tamaño, firma ni ruta.

Responsabilidades:

- **Escribir** un archivo YA validado en `MEDIA_ROOT/productos/<id>/<uuid><ext>`
  (FR-06 §2.2). El nombre enviado por el cliente se ignora y la extensión sale
  del MIME detectado.
- **Limpiar** en los caminos obligatorios de FR-06 §2.5: validación fallida
  (nada escrito), rollback de la transacción, reemplazo y borrado.
- **Degradar** con aviso cuando el archivo ya no existe en disco (FR-06 §2.7).

El servicio es SYNC y NO abre transacción: la atomicidad la aporta el flujo.
"""

import logging

from django.core.files.storage import default_storage
from django.db.models.fields.files import FieldFile

from core.exceptions import MediaTipoNoPermitidoError, MediaTokenNoResueltoError
from core.media import (
    construir_ruta_media,
    limpiar_archivos_media,
    media_root,
    url_publica_media,
)

from modules.marketplace.domain.constants import DOMINIO_MEDIA
from modules.marketplace.domain.models import ProductoImagen

logger = logging.getLogger(__name__)


class ProductoMediaService:
    """Escritura, reemplazo y limpieza de los archivos de un producto."""

    # ── Ruta ────────────────────────────────────────────────────────────────

    def ruta_relativa(self, producto_id, extension: str) -> str:
        """`productos/<producto_id>/<uuid><ext>` (FR-06 §2.2).

        El UUID lo genera el servidor y la extensión viene del MIME
        DETECTADO. Un `ValueError` del constructor compartido se traduce al
        código de media del catálogo: nunca sale texto crudo al cliente.
        """
        from core.media import allowed_domains

        if DOMINIO_MEDIA not in allowed_domains():
            raise MediaTipoNoPermitidoError()
        try:
            return construir_ruta_media(DOMINIO_MEDIA, producto_id, extension)
        except ValueError:
            raise MediaTipoNoPermitidoError() from None

    # ── Escritura ───────────────────────────────────────────────────────────

    def escribir(self, producto, imagen, orden: int, rutas_escritas: list) -> ProductoImagen:
        """Persiste una imagen de la galería y devuelve la fila creada.

        `rutas_escritas` es la lista de rutas escritas durante la operación:
        el flujo la usa para limpiar si la transacción falla. La ruta se
        registra ANTES de escribir para que un fallo posterior no deje un
        archivo huérfano en el volumen.
        """
        upload = getattr(imagen, "upload", None)
        if upload is None:
            raise MediaTokenNoResueltoError()

        ruta = self.ruta_relativa(producto.id, upload.extension)
        rutas_escritas.append(ruta)

        instancia = ProductoImagen(
            producto=producto,
            orden=orden,
            es_principal=bool(getattr(imagen, "es_principal", False)),
            texto_alternativo=getattr(imagen, "texto_alternativo", "") or "",
        )
        instancia.ruta_media_previa = ruta
        instancia.imagen = self._preparar_archivo(instancia, upload.archivo)
        instancia.save()

        # La ruta definitiva puede diferir de la prevista si el storage
        # desambiguó un choque de nombre: se registra la real.
        rutas_escritas[-1] = instancia.imagen.name
        return instancia

    @staticmethod
    def _preparar_archivo(instancia, archivo):
        """Envuelve el archivo subido en el `FieldFile` del campo.

        El `FieldFile` con `_committed = False` es lo que hace que Django
        escriba el archivo EN EL MOMENTO del `save()`, aplicando el
        `upload_to` (ruta precalculada) y el storage configurado.
        """
        campo = ProductoImagen._meta.get_field("imagen")
        envuelto = FieldFile(instancia, campo, getattr(archivo, "name", "") or "")
        envuelto.file = archivo
        envuelto._committed = False
        return envuelto

    # ── Reemplazo ───────────────────────────────────────────────────────────

    def reemplazar(self, producto, imagen_previa, upload, rutas_escritas: list) -> ProductoImagen:
        """Reemplaza el archivo de una imagen existente.

        FR-06 §2.5: el archivo anterior se borra DESPUÉS de que el nuevo
        quedó persistido con éxito. Si la escritura falla, el anterior sigue
        en su sitio y el nuevo se limpia.
        """
        ruta = self.ruta_relativa(producto.id, upload.extension)
        rutas_escritas.append(ruta)

        instancia = imagen_previa
        ruta_previa = instancia.imagen.name if instancia.imagen else ""
        instancia.ruta_media_previa = ruta
        instancia.imagen = self._preparar_archivo(instancia, upload.archivo)
        instancia.save(update_fields=["imagen", "updated_at"])
        rutas_escritas[-1] = instancia.imagen.name

        # El archivo anterior se borra DESPUÉS de que el nuevo quedó
        # persistido (FR-06 §2.5).
        if ruta_previa and ruta_previa != instancia.imagen.name:
            limpiar_archivos_media([ruta_previa])
        return instancia

    # ── Limpieza ────────────────────────────────────────────────────────────

    @staticmethod
    def limpiar(rutas) -> list[str]:
        """Borra los archivos indicados y devuelve las rutas eliminadas."""
        return limpiar_archivos_media(rutas)

    def eliminar_archivos_de(self, imagenes) -> list[str]:
        """Borra los archivos de las imágenes indicadas (borrado de entidad)."""
        rutas = [imagen.imagen.name for imagen in imagenes if imagen.imagen and imagen.imagen.name]
        return self.limpiar(rutas)

    # ── Lectura para la presentación ────────────────────────────────────────

    @staticmethod
    def url_de(ruta: str) -> str:
        """URL pública de una ruta de media."""
        return url_publica_media(ruta)

    @staticmethod
    def disponible(ruta: str) -> bool:
        """Si el archivo sigue existiendo en el volumen.

        FR-06 §2.7: si la foto deja de existir, la galería degrada con aviso
        y se registra una incidencia de media (log), sin error 500.
        """
        if not ruta:
            return False
        existe = default_storage.exists(ruta)
        if not existe:
            logger.warning(
                "Incidencia de media: el archivo %s no existe bajo %s.",
                ruta,
                media_root(),
            )
        return existe


__all__ = ["ProductoMediaService"]
