"""Vocabulario cerrado del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md` ·
          `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`

Este módulo NO declara un vocabulario de estados comerciales: un patrocinador
tiene una única característica de ciclo de vida, la **VISIBILIDAD** (booleana),
que ADM-21 nombra y ningún contrato congela como enumeración. Se modela como
un `BooleanField` y no como una lista de estados inventada.

Dos constantes:

1. `DOMINIO_MEDIA` — el primer segmento de la ruta de almacenamiento de los
   archivos del módulo: `MEDIA_ROOT/patrocinadores/<patrocinador_id>/<uuid><ext>`
   (FR-06 §2.2). El valor está autorizado en `settings.MEDIA_DOMAINS`.
2. `MODULO_LOGICO` — la clave del módulo lógico que habilita los patrocinadores
   en una edición (FR-02 §2.5, RN-E02). La clave ya existe en el catálogo
   cerrado de `eventos` (`ModuloLogico.PATROCINADORES`).

Este archivo NO declara ninguna constante de "edición activa": el alcance se
resuelve con el ORDEN ÚNICO de FR-02 §2.2, que vive en el módulo `eventos`.
"""

#: Primer segmento autorizado de la ruta de media del módulo (FR-06 §2.2).
DOMINIO_MEDIA = "patrocinadores"

#: Clave del módulo lógico que habilita los patrocinadores en una edición.
MODULO_LOGICO = "patrocinadores"

#: Tope de imágenes de la galería de un patrocinador.
#:
#: Es un LÍMITE ESTRUCTURAL del recurso (el carrusel es un carrusel, no un
#: álbum), declarado de forma explícita para que el rechazo sea reproducible y
#: no dependa de un valor implícito. No es una política comercial.
MAX_IMAGENES_GALERIA = 24


__all__ = [
    "DOMINIO_MEDIA",
    "MAX_IMAGENES_GALERIA",
    "MODULO_LOGICO",
]
