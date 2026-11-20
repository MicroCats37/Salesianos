"""`AdminAuditoriaSelector` — la lectura del ACTA transversal.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Sólo LECTURA del modelo propio del módulo. Aquí no hay reglas de negocio: el
acta ya está escrita. La SANITIZACIÓN ocurre al escribir (el servicio) y la
LISTA BLANCA al publicar (el presenter); el selector sólo pagina.
"""

from modules.administracion.domain.models import AccionAuditada
from modules.administracion.domain.results.admin_resultados import (
    AuditoriaItemResultado,
    AuditoriaListadoResultado,
)


class AdminAuditoriaSelector:
    """Lectura paginada del acta de auditoría."""

    def listar(
        self,
        edicion_id=None,
        accion=None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditoriaListadoResultado:
        """Las actas de la página pedida, de la más reciente a la más antigua.

        `edicion_id` y `accion` son filtros OPCIONALES y exactos: un filtro
        desconocido no devuelve un conjunto vacío silencioso, devuelve la
        lista sin ese filtro porque el selector sólo aplica los que recibió.
        """
        queryset = AccionAuditada.objects.all()

        if edicion_id:
            queryset = queryset.filter(edicion_id=edicion_id)

        if accion:
            queryset = queryset.filter(accion=accion)

        queryset = queryset.order_by("-created_at")

        total = queryset.count()
        pagina = max(page, 1)
        tamano = max(page_size, 1)
        inicio = (pagina - 1) * tamano
        filas = list(queryset[inicio:inicio + tamano])

        return AuditoriaListadoResultado(
            items=[
                AuditoriaItemResultado(
                    id=str(fila.id),
                    edicion_id=str(fila.edicion_id) if fila.edicion_id else None,
                    actor=fila.actor_nombre or "Sistema",
                    accion=fila.accion,
                    entidad=fila.entidad,
                    entidad_id=fila.entidad_id,
                    motivo=fila.motivo,
                    registrado_en=fila.created_at,
                )
                for fila in filas
            ],
            total=total,
            page=pagina,
            page_size=tamano,
            total_pages=(total + tamano - 1) // tamano,
        )


__all__ = ["AdminAuditoriaSelector"]
