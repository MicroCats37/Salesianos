"""Módulo de VIDEOS: la sala de proyección pública del festival.

Change: `public-video-streaming-crud`

Contrato de datos (aprobado):

    Video
      id: UUID             (pk)
      titulo: str
      descripcion: str
      url: str
      created_at, updated_at

El módulo es DELIBERADAMENTE mínimo: **todos** los videos son públicos, no
hay bandera `es_publico`, ni proveedor, ni subidas, ni categorías, ni claves
foráneas a otros dominios. La entidad es editorial y no pertenece a ninguna
edición: es un contenido de la SALA DE PROYECCIÓN del evento.

La seguridad de la URL es una regla de DOS capas:

1. el SERVIDOR sólo admite `http` y `https` (`domain/exceptions.py` ·
   `VideoUrlInvalidaError`), de modo que `javascript:`, `data:` y `ftp:` nunca
   llegan a persistirse;
2. el CLIENTE clasifica la URL en un archivo reproducible, un embed de un
   proveedor permitido o un enlace externo (`features/videos/utils`), y nunca
   usa `dangerouslySetInnerHTML` ni `srcDoc`.
"""

default_app_config = "modules.videos.apps.VideosConfig"
