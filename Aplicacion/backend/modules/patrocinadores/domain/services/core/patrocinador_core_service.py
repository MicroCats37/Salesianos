"""`PatrocinadorCoreService` — escritura y proyección de los patrocinadores.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.3 (core services)

El core service es SYNC y **NO abre `transaction.atomic()`**: la atomicidad
compuesta la aporta el flujo.

Reglas que este servicio es el dueño de:

- **Coherencia de edición** (FR-02 §3 · RN-E01): el patrocinador y su galería
  tienen que pertenecer a la MISMA edición. La coherencia es estructural.
- **Coherencia de la galería**: la galería tiene un tope declarado; la
  comprobación ocurre ANTES de escribir un solo archivo, para que un rechazo no
  deje residuos en el volumen (FR-06 §2.5).
- **Visibilidad** (ADM-21): `visible` es un hecho del patrocinador, no una
  configuración de despliegue.
- **SIN FINANZAS**: este módulo no modela aportaciones, comisiones, pagos,
  facturas ni contabilidad de terceros (ADM-21, `funcional/01`).
"""

from modules.patrocinadores.domain.constants import MAX_IMAGENES_GALERIA
from modules.patrocinadores.domain.exceptions import (
    GaleriaPatrocinadorInvalidaError,
    PatrocinadorImagenNoEncontradaError,
)
from modules.patrocinadores.domain.models import Patrocinador
from modules.patrocinadores.domain.results.patrocinadores_result import (
    PatrocinadorImagenResult,
    PatrocinadorLogoResult,
    PatrocinadorResult,
)
from modules.patrocinadores.domain.selectors.patrocinador_selector import (
    PatrocinadorSelector,
)
from modules.patrocinadores.domain.services.core.patrocinador_media_service import (
    PatrocinadorMediaService,
)


class PatrocinadorCoreService:
    """Operaciones de escritura y proyección de los patrocinadores."""

    def __init__(
        self,
        patrocinador_selector: PatrocinadorSelector = None,
        media_service: PatrocinadorMediaService = None,
    ):
        self.patrocinador_selector = patrocinador_selector or PatrocinadorSelector()
        self.media_service = media_service or PatrocinadorMediaService()

    # ── Alta ────────────────────────────────────────────────────────────────

    def crear(self, data) -> Patrocinador:
        """Crea un patrocinador dentro del alcance de edición indicado.

        El alcance (edición) lo resuelve el SERVIDOR: el cliente nunca elige
        la edición a la que escribe (el orquestador sustituye el
        `edicion_id` del payload por la edición vigente).
        """
        self.validar_galeria(data.imagenes or [])

        return Patrocinador.objects.create(
            edicion_id=data.edicion_id,
            nombre=data.nombre,
            slug=data.slug,
            descripcion=data.descripcion or "",
            sitio_web=data.sitio_web or "",
            visible=bool(data.visible),
        )

    @staticmethod
    def validar_galeria(imagenes) -> None:
        """Coherencia de la galería antes de ESCRIBIR un solo archivo.

        El tope es un límite estructural del recurso, declarado de forma
        explícita (`MAX_IMAGENES_GALERIA`): un rechazo explícito es mejor que
        un carrusel sin fin.
        """
        if len(imagenes or []) > MAX_IMAGENES_GALERIA:
            raise GaleriaPatrocinadorInvalidaError()

    # ── Edición de la ficha ─────────────────────────────────────────────────

    def actualizar(self, patrocinador: Patrocinador, data) -> Patrocinador:
        """Actualización parcial de la ficha y de la visibilidad.

        NO toca el logo ni la galería: los archivos tienen su propio camino de
        escritura (reemplazo) y su propia política de limpieza (FR-06 §2.5).
        """
        campos = data.model_dump(exclude_unset=True, exclude_none=True)
        for campo, valor in campos.items():
            setattr(patrocinador, campo, valor)
        patrocinador.save()
        return patrocinador

    # ── Orden de la galería ─────────────────────────────────────────────────

    def reordenar_imagenes(self, patrocinador: Patrocinador, ordenes) -> list:
        """Fija el orden canónico de las imágenes de la galería.

        `ordenes` es la lista de `PatrocinadorOrdenImagenData`: cada entrada
        declara el identificador de UNA imagen y su posición. Una imagen que no
        pertenece al patrocinador se rechaza: el orden NUNCA cruza el alcance.

        El orden canónico sigue siendo `orden ASC, id ASC` (FR-06 §2.6): dos
        imágenes con la misma posición siguen teniendo un orden determinista.
        """
        imagenes = self.patrocinador_selector.listar_imagenes(patrocinador.id)
        por_id = {str(imagen.id): imagen for imagen in imagenes}

        for entrada in ordenes or []:
            imagen = por_id.get(str(entrada.imagen_id))
            if imagen is None:
                raise PatrocinadorImagenNoEncontradaError()
            imagen.orden = int(entrada.orden)
            imagen.save(update_fields=["orden", "updated_at"])

        return self.patrocinador_selector.listar_imagenes(patrocinador.id)

    # ── Proyección a results ────────────────────────────────────────────────

    def result_de(self, patrocinador: Patrocinador, imagenes=None) -> PatrocinadorResult:
        """Proyecta un patrocinador (con su galería) al result object."""
        if imagenes is None:
            imagenes = self.patrocinador_selector.listar_imagenes(patrocinador.id)

        ruta_logo = patrocinador.logo.name if patrocinador.logo else ""
        logo = None
        if ruta_logo:
            disponible = self.media_service.disponible(ruta_logo)
            logo = PatrocinadorLogoResult(
                url=self.media_service.url_de(ruta_logo) if disponible else None,
                disponible=disponible,
            )

        return PatrocinadorResult(
            id=patrocinador.id,
            edicion_id=patrocinador.edicion_id,
            edicion_nombre=getattr(getattr(patrocinador, "edicion", None), "nombre", "") or "",
            nombre=patrocinador.nombre,
            slug=patrocinador.slug,
            descripcion=patrocinador.descripcion or "",
            sitio_web=patrocinador.sitio_web or "",
            visible=bool(patrocinador.visible),
            logo=logo,
            imagenes=[self.result_imagen(imagen) for imagen in imagenes],
            created_at=patrocinador.created_at,
            updated_at=patrocinador.updated_at,
        )

    def result_imagen(self, imagen) -> PatrocinadorImagenResult:
        """Proyecta una imagen al result object, degradando si falta el archivo."""
        ruta = imagen.imagen.name if imagen.imagen else ""
        disponible = self.media_service.disponible(ruta)
        return PatrocinadorImagenResult(
            id=imagen.id,
            orden=imagen.orden,
            url=self.media_service.url_de(ruta) if disponible else None,
            texto_alternativo=imagen.texto_alternativo or "",
            disponible=disponible,
            created_at=imagen.created_at,
        )


__all__ = ["PatrocinadorCoreService"]
