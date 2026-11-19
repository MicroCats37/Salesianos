"""`EdicionCoreService` — escrituras sobre `Edicion`.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §4.3 (core services)

El core service es SYNC y **NO abre `transaction.atomic()`**: la atomicidad
compuesta la aporta el flujo (`domain/services/flujos/edicion_flujo.py`).

Todas las escrituras exigen una edición YA RESUELTA: el servicio no resuelve
alcance. La resolución vive en `EdicionScopeService` y su resultado viaja como
argumento explícito, de modo que ninguna escritura puede operar sobre "la
edición que haya" (FR-02 §2.2, regla dura).

Las violaciones de `UniqueConstraint` llegan aquí como `IntegrityError`; las
traduce a excepciones de dominio el flujo, que es quien posee la transacción.
"""

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.exceptions import (
    EventoNoEncontradoError,
    ModuloNoHabilitadoError,
)
from modules.eventos.domain.models import Edicion
from modules.eventos.domain.schemas.edicion_schemas import (
    EdicionCreateData,
    EdicionUpdateData,
)
from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector


class EdicionCoreService:
    """Operaciones de escritura sobre ediciones."""

    def __init__(
        self,
        edicion_selector: EdicionSelector = None,
        evento_selector: EventoSelector = None,
    ):
        self.edicion_selector = edicion_selector or EdicionSelector()
        self.evento_selector = evento_selector or EventoSelector()

    # ── Alta ────────────────────────────────────────────────────────────────

    def crear(self, data: EdicionCreateData) -> Edicion:
        """Crea una edición en estado `BORRADOR`.

        El evento debe existir; el slug debe ser único DENTRO del evento
        (FR-02 §3). El alta NUNCA publica: publicar es una transición
        posterior con su propia regla.

        Puede lanzar `IntegrityError` si el slug ya existe en el evento; el
        flujo lo traduce a `EdicionSlugDuplicadoError`.
        """
        evento = self.evento_selector.obtener_por_id(data.evento_id)
        if evento is None:
            raise EventoNoEncontradoError()

        return Edicion.objects.create(
            evento=evento,
            nombre=data.nombre,
            slug=data.slug,
            anio=data.anio,
            estado=EstadoEdicion.BORRADOR,
            modulos_habilitados=list(data.modulos_habilitados or []),
            fecha_inicio=data.fecha_inicio,
            fecha_fin=data.fecha_fin,
        )

    # ── Actualización ───────────────────────────────────────────────────────

    def actualizar(self, edicion: Edicion, data: EdicionUpdateData) -> Edicion:
        """Actualización parcial. NO cambia el estado de la edición."""
        campos = data.model_dump(exclude_unset=True, exclude_none=True)
        for campo, valor in campos.items():
            setattr(edicion, campo, valor)
        edicion.save()
        return edicion

    # ── Transiciones ────────────────────────────────────────────────────────

    def publicar(self, edicion: Edicion) -> Edicion:
        """Publica la edición.

        La invariante "como máximo una edición `PUBLICADA` por evento" la
        impone la `UniqueConstraint` condicional de la base de datos: es la
        autoridad final y dos publicaciones simultáneas no pueden coexistir.

        Puede lanzar `IntegrityError` cuando el evento ya tiene una edición
        publicada; el flujo lo traduce a `EdicionPublicadaDuplicadaError`.
        """
        if edicion.estado == EstadoEdicion.PUBLICADA:
            return edicion
        edicion.estado = EstadoEdicion.PUBLICADA
        edicion.save(update_fields=["estado", "updated_at"])
        return edicion

    def cerrar(self, edicion: Edicion) -> Edicion:
        """Cierra la edición (`CERRADA`). El histórico se conserva (RN-E01)."""
        edicion.estado = EstadoEdicion.CERRADA
        edicion.save(update_fields=["estado", "updated_at"])
        return edicion

    # ── Habilitación de módulos (RN-E02) ────────────────────────────────────

    @staticmethod
    def exigir_modulo(edicion: Edicion, clave: str) -> None:
        """Verifica que el módulo lógico esté habilitado en la edición.

        Un módulo no habilitado no expone catálogo ni rutas de escritura
        (FR-02 §2.5). El valor por defecto es DESHABILITADO.
        """
        if not edicion.modulo_habilitado(clave):
            raise ModuloNoHabilitadoError()


__all__ = ["EdicionCoreService"]
