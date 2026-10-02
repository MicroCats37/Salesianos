"""
DisciplinaService — sync CRUD operations for Disciplina and Categoria.

Core service — no transaction.atomic own, no async.
"""

from injector import inject

from modules.inscripciones.domain.models import Disciplina, Categoria
from modules.inscripciones.domain.schemas import (
    DisciplinaCreateData,
    DisciplinaUpdateData,
    CategoriaCreateData,
    CategoriaUpdateData,
)


class DisciplinaService:
    """
    Core service for Disciplina and Categoria operations.
    """

    @inject
    def __init__(self):
        pass

    # ── Disciplina ────────────────────────────────────────────────────────────

    def crear(self, data: DisciplinaCreateData) -> Disciplina:
        """Create a new Disciplina."""
        return Disciplina.objects.create(
            nombre=data.nombre,
            sigla=data.sigla,
            modalidad=data.modalidad,
            min_jugadores=data.min_jugadores,
            max_jugadores=data.max_jugadores,
            esta_activa=data.esta_activa,
        )

    def actualizar(self, disciplina: Disciplina, data: DisciplinaUpdateData) -> Disciplina:
        """Update an existing Disciplina."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(disciplina, field, value)
        disciplina.save()
        return disciplina

    def obtener(self, disciplina_id: str) -> Disciplina | None:
        """Get a Disciplina by ID."""
        return Disciplina.objects.filter(id=disciplina_id).first()

    def listar_activas(self) -> list[Disciplina]:
        """List all active Disciplinas."""
        return list(Disciplina.objects.filter(esta_activa=True).order_by("nombre"))

    def listar_todas(self) -> list[Disciplina]:
        """List all Disciplinas regardless of status."""
        return list(Disciplina.objects.order_by("nombre"))

    # ── Categoria ────────────────────────────────────────────────────────────

    def crear_categoria(self, data: CategoriaCreateData) -> Categoria:
        """Create a new Categoria."""
        return Categoria.objects.create(
            disciplina_id=data.disciplina_id,
            nombre=data.nombre,
            anio_minimo=data.anio_minimo,
            anio_maximo=data.anio_maximo,
            esta_activa=data.esta_activa,
        )

    def actualizar_categoria(self, categoria: Categoria, data: CategoriaUpdateData) -> Categoria:
        """Update an existing Categoria."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(categoria, field, value)
        categoria.save()
        return categoria

    def obtener_categoria(self, categoria_id: str) -> Categoria | None:
        """Get a Categoria by ID."""
        return Categoria.objects.filter(id=categoria_id).first()

    def listar_categorias_por_disciplina(self, disciplina_id: str) -> list[Categoria]:
        """List active categories for a discipline."""
        return list(
            Categoria.objects
            .filter(disciplina_id=disciplina_id, esta_activa=True)
            .order_by("anio_minimo")
        )

    def listar_categorias_activas(self) -> list[Categoria]:
        """List all active categorias."""
        return list(
            Categoria.objects
            .filter(esta_activa=True)
            .select_related("disciplina")
            .order_by("disciplina__nombre", "anio_minimo")
        )
