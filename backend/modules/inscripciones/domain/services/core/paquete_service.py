"""
PaqueteService — sync CRUD operations for Paquete and PaqueteDisciplina.

Core service — no transaction.atomic own, no async.
"""

from injector import inject

from modules.inscripciones.domain.models import Paquete, PaqueteDisciplina, Disciplina


class PaqueteService:
    """
    Core service for Paquete and PaqueteDisciplina operations.
    """

    @inject
    def __init__(self):
        pass

    # ── Paquete ──────────────────────────────────────────────────────────────

    def crear(self, data) -> Paquete:
        """Create a new Paquete."""
        return Paquete.objects.create(
            nombre=data.nombre,
            descripcion=data.descripcion,
            cantidad_maxima_participantes=data.cantidad_maxima_participantes,
            precio_regular=data.precio_regular,
            precio_promocional=data.precio_promocional,
            valido_desde=data.valido_desde,
            valido_hasta=data.valido_hasta,
            esta_activo=data.esta_activo,
        )

    def actualizar(self, paquete: Paquete, data) -> Paquete:
        """Update an existing Paquete."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(paquete, field, value)
        paquete.save()
        return paquete

    def obtener(self, paquete_id: str) -> Paquete | None:
        """Get a Paquete by ID."""
        return Paquete.objects.filter(id=paquete_id).first()

    def listar_activos(self) -> list[Paquete]:
        """List all active Paquetes."""
        return list(
            Paquete.objects
            .filter(esta_activo=True)
            .prefetch_related("paquete_disciplinas__disciplina")
            .order_by("nombre")
        )

    def listar_todos(self) -> list[Paquete]:
        """List all Paquetes regardless of status."""
        return list(Paquete.objects.order_by("nombre"))

    # ── PaqueteDisciplina ────────────────────────────────────────────────────

    def agregar_disciplina(self, paquete_id: str, disciplina_id: str) -> PaqueteDisciplina:
        """Add a discipline to a package."""
        return PaqueteDisciplina.objects.create(
            paquete_id=paquete_id,
            disciplina_id=disciplina_id,
        )

    def quitar_disciplina(self, paquete_id: str, disciplina_id: str) -> int:
        """Remove a discipline from a package. Returns number of deleted rows."""
        return PaqueteDisciplina.objects.filter(
            paquete_id=paquete_id,
            disciplina_id=disciplina_id,
        ).delete()[0]

    def listar_disciplinas_de_paquete(self, paquete_id: str) -> list[Disciplina]:
        """List all disciplines included in a package."""
        return list(
            Disciplina.objects
            .filter(paquete_disciplinas__paquete_id=paquete_id)
            .order_by("nombre")
        )

    def disciplna_esta_en_paquete(self, paquete_id: str, disciplina_id: str) -> bool:
        """Check if a discipline is included in a package."""
        return PaqueteDisciplina.objects.filter(
            paquete_id=paquete_id,
            disciplina_id=disciplina_id,
        ).exists()
