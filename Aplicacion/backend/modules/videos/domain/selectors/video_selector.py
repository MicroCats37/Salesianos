"""Selectores del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

REGLA (F-26): un selector que devuelve un `QuerySet` es una mina en un
contexto async: la consulta es perezosa y recorrerla dentro de una función
async lanza `SynchronousOnlyOperation`. Por eso TODOS los selectores de este
módulo devuelven LISTAS ya evaluadas.

El orden canónico del modelo es `-created_at` (lo más nuevo primero). El
listado administrativo admite una lista BLANCA de columnas de orden: el
cliente nunca decide una columna de la base de datos.
"""

from modules.videos.domain.models import Video

#: Columnas por las que el listado administrativo admite ordenar.
COLUMNAS_ORDEN = ("created_at", "updated_at", "titulo")


class VideoSelector:
    """Consultas de lectura sobre `Video`."""

    def listar(self) -> list[Video]:
        """Todos los videos, en el orden canónico (`-created_at`).

        El listado PÚBLICO usa esta lectura: la galería es pequeña y el
        servidor devuelve la lista completa, sin paginar.
        """
        return list(Video.objects.all())

    def listar_paginado(
        self,
        q: str | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Video], int]:
        """Una página del listado administrativo y el total del filtro.

        `q` busca por título o descripción (contiene, sin distinguir mayúsculas)
        y `ordering` es una columna de la lista blanca, con el prefijo `-` para
        el orden inverso.
        """
        consulta = Video.objects.all()

        texto = (q or "").strip()
        if texto:
            consulta = consulta.filter(titulo__icontains=texto) | consulta.filter(
                descripcion__icontains=texto
            )

        consulta = consulta.distinct().order_by(self._orden_de(ordering))

        total = consulta.count()
        inicio = max(0, (page - 1) * page_size)
        return list(consulta[inicio : inicio + page_size]), total

    def obtener_por_id(self, video_id) -> Video | None:
        """Un video por identificador, o `None`."""
        return Video.objects.filter(id=video_id).first()

    def contar(self, q: str | None = None) -> int:
        """Cuántos videos hay (con el filtro de texto, si lo hay)."""
        consulta = Video.objects.all()

        texto = (q or "").strip()
        if texto:
            consulta = consulta.filter(titulo__icontains=texto) | consulta.filter(
                descripcion__icontains=texto
            )

        return consulta.distinct().count()

    @staticmethod
    def _orden_de(ordering: str | None) -> str:
        """La columna de orden, o la canónica si la pedida no existe.

        La lista blanca es la del módulo: una columna desconocida NO llega a la
        base de datos.
        """
        if not ordering:
            return "-created_at"

        inversa = ordering.startswith("-")
        columna = ordering[1:] if inversa else ordering

        if columna not in COLUMNAS_ORDEN:
            return "-created_at"

        return f"-{columna}" if inversa else columna


__all__ = ["COLUMNAS_ORDEN", "VideoSelector"]
