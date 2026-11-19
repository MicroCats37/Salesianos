"""`EdicionSelector` — superficie de lectura de ediciones.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector es DE SOLO LECTURA por construcción: ningún método escribe.

Sobre el selector congelado (`backend/modules/eventos/domain/selectors/`)
este selector NO tiene ningún método "activo":

- NO existe `obtener_activo()` (la edición "más reciente").
- NO existe `obtener_activo_por_nombre()` (la edición "por defecto").
- NO existe ninguna lectura de la constante de "evento activo" de settings.

La resolución de alcance es un ORDEN ÚNICO y vive en
`modules/eventos/domain/services/core/edicion_scope_service.py`
(FR-02 §2.2). Aquí sólo hay consultas; la decisión, en el servicio.

Regla de identificadores (FR-02 §2.3 #2): el scope se resuelve por `id`, o por
`slug` RESUELTO a `id` en el borde de entrada. Nunca por nombre.
"""

import uuid

from django.db.models import QuerySet

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.models import Edicion


def _normalizar_uuid(valor) -> uuid.UUID | None:
    """Convierte a `uuid.UUID` o devuelve `None` si el valor no es un UUID.

    Un identificador mal formado NO es una excepción: es "no existe". Así el
    borde de entrada responde 404 en lugar de 500.
    """
    if isinstance(valor, uuid.UUID):
        return valor
    if valor in (None, ""):
        return None
    try:
        return uuid.UUID(str(valor))
    except (AttributeError, TypeError, ValueError):
        return None


class EdicionSelector:
    """Consultas de solo lectura sobre `Edicion`."""

    def obtener_por_id(self, edicion_id) -> Edicion | None:
        """La edición con ese identificador, o `None` si no existe."""
        identificador = _normalizar_uuid(edicion_id)
        if identificador is None:
            return None
        return Edicion.objects.filter(id=identificador).first()

    def obtener_por_slug(self, evento_id, slug: str) -> Edicion | None:
        """La edición con ese slug DENTRO del evento indicado, o `None`."""
        identificador = _normalizar_uuid(evento_id)
        if identificador is None:
            return None
        return Edicion.objects.filter(
            evento_id=identificador,
            slug=slug,
        ).first()

    def obtener_publicada(self) -> Edicion | None:
        """La edición `PUBLICADA`, sólo si hay EXACTAMENTE una.

        Devuelve `None` cuando no hay ninguna o cuando hay más de una: la
        distinción entre "cero" y "demasiadas" la hace el servicio de alcance
        con `contar_publicadas()`, porque las dos situaciones producen
        errores DISTINTOS (FR-02 §2.2 #3).
        """
        return self.listar_publicadas().first() if self.contar_publicadas() == 1 else None

    def contar_publicadas(self) -> int:
        """Cuántas ediciones `PUBLICADA` existen en el sistema."""
        return Edicion.objects.filter(estado=EstadoEdicion.PUBLICADA).count()

    def contar(self) -> int:
        """Cuántas ediciones existen en el sistema (cualquier estado)."""
        return Edicion.objects.count()

    def listar_publicadas(self) -> QuerySet[Edicion]:
        """Las ediciones `PUBLICADA`, en orden estable."""
        return (
            Edicion.objects.filter(estado=EstadoEdicion.PUBLICADA)
            .select_related("evento")
            .order_by("-anio", "nombre")
        )

    def listar_por_evento(self, evento_id) -> QuerySet[Edicion]:
        """Las ediciones de UN evento. Es el filtro anti-fuga por defecto."""
        identificador = _normalizar_uuid(evento_id)
        if identificador is None:
            return Edicion.objects.none()
        return (
            Edicion.objects.filter(evento_id=identificador)
            .select_related("evento")
            .order_by("-anio", "nombre")
        )

    def listar(self) -> QuerySet[Edicion]:
        """Todas las ediciones del sistema.

        Un listado sin `edicion_id` DEBE declarar en su contrato qué ediciones
        incluye (FR-02 §2.3 #5). Este selector existe para administración y
        su contrato es "todas las ediciones, de todos los eventos".
        """
        return Edicion.objects.select_related("evento").order_by("-anio", "nombre")


__all__ = ["EdicionSelector"]
