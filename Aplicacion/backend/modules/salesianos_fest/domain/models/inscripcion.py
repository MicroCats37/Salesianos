"""Inscripción del responsable y sus equipos.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Invariantes:

- **Una inscripción tiene un RESPONSABLE** (`RN-I01`): `responsable` es una
  `usuarios.Persona`, no un documento suelto ni un id de cuenta.
- **La inscripción pertenece a UNA edición** (`RN-E01`): conserva su propio
  catálogo, sus compras y su historial.
- **La inscripción declara su PROMOCIÓN** (`D-CAT-01`): `promocion` es la
  cohorte que compra. Es OBLIGATORIA y es la que determina la categoría.
- **La fusión es DESCRIPTIVA** (`D-CAT-02`): `fusion_promocion` nombra la
  segunda cohorte de una promoción fusionada. NO cambia cupos, ni pago, ni
  categoría, ni elegibilidad de equipo, ni cuadro competitivo.
- **La categoría del equipo la DERIVA el servidor** (`D-CAT-05`): `Equipo`
  no acepta una categoría del cliente; sale de `Inscripcion.promocion` contra
  el rango de la `Categoria` de la edición.
- **Los cupos PAGADOS empiezan en cero** (`RN-I02`, `QA-I01`): una compra
  pendiente no habilita ningún cupo. `cupos_pagados` sólo lo incrementa la
  ACTIVACIÓN de derechos, que es de `DOM-02` a través del puerto congelado
  `IActivadorDominioCompra`.
- **No se duplica la inscripción** de un responsable en la misma edición con
  el mismo paquete: lo garantiza la restricción única condicional de la base
  de datos, no una comprobación de aplicación.
- **El saldo disponible nunca es negativo** (`RN-I03`): es la diferencia entre
  cupos pagados y asignados, y ambos se derivan del servidor.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6).
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import (
    EstadoEquipo,
    EstadoInscripcion,
)


class Inscripcion(BaseModel):
    """Inscripción deportiva de un responsable en una edición."""

    history = HistoricalRecords()

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Edición",
    )
    responsable = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Responsable",
        help_text=(
            "La persona que responde por la inscripción. La cuenta "
            "autenticada puede ser otra: la titularidad la decide el "
            "responsable, no el rol (`FR-03` §2.1)."
        ),
    )
    paquete = models.ForeignKey(
        "salesianos_fest.Paquete",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Paquete",
    )
    promocion = models.ForeignKey(
        "salesianos_fest.Promocion",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Promoción",
        help_text=(
            "Cohorte que compra la inscripción. Es OBLIGATORIA y es la que "
            "determina la categoría del equipo (`D-CAT-01`)."
        ),
    )
    fusion_promocion = models.ForeignKey(
        "salesianos_fest.Promocion",
        on_delete=models.PROTECT,
        related_name="inscripciones_fusionadas",
        null=True,
        blank=True,
        verbose_name="Promoción fusionada",
        help_text=(
            "Segunda cohorte de una promoción FUSIONADA. Es DESCRIPTIVA: no "
            "altera cupos, pago, categoría, elegibilidad ni cuadro "
            "competitivo (`D-CAT-02`)."
        ),
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoInscripcion.choices,
        default=EstadoInscripcion.CREADA,
        verbose_name="Estado",
    )
    referencia = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="Referencia",
        help_text=(
            "Referencia estable de la inscripción. Identifica la intención de "
            "compra para que un reintento NO cree una segunda compra."
        ),
    )
    cupos_solicitados = models.PositiveIntegerField(
        default=1,
        verbose_name="Cupos solicitados",
        help_text="Cupos que la inscripción compra en su alta.",
    )
    cupos_pagados = models.PositiveIntegerField(
        default=0,
        verbose_name="Cupos pagados",
        help_text=(
            "CERO hasta que la activación de derechos verifique el pago. "
            "Una compra pendiente no habilita cupos (`RN-I02`)."
        ),
    )
    cupos_asignados = models.PositiveIntegerField(
        default=0,
        verbose_name="Cupos asignados",
    )

    class Meta:
        db_table = "fest_inscripcion"
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ["-created_at"]
        constraints = [
            # Una inscripción viva por (edición, responsable, paquete): un
            # reintento del alta NO puede duplicar la inscripción.
            models.UniqueConstraint(
                fields=["edicion", "responsable", "paquete"],
                condition=~models.Q(estado=EstadoInscripcion.CANCELADA),
                name="fest_inscripcion_unica_por_responsable_y_paquete",
            ),
            # El saldo nunca es negativo (`RN-I03`).
            models.CheckConstraint(
                condition=models.Q(cupos_asignados__lte=models.F("cupos_pagados")),
                name="fest_inscripcion_asignados_no_superan_pagados",
            ),
        ]

    def __str__(self) -> str:
        return f"Inscripción {self.id} ({self.edicion_id})"


class Equipo(BaseModel):
    """Equipo declarado por el responsable dentro de su inscripción."""

    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="equipos",
        verbose_name="Inscripción",
    )
    disciplina = models.ForeignKey(
        "salesianos_fest.Disciplina",
        on_delete=models.PROTECT,
        related_name="equipos",
        verbose_name="Disciplina",
    )
    categoria = models.ForeignKey(
        "salesianos_fest.Categoria",
        on_delete=models.PROTECT,
        related_name="equipos",
        verbose_name="Categoría",
        help_text=(
            "Banda competitiva del equipo. La DERIVA el servidor desde la "
            "promoción de la inscripción: el cliente no la declara "
            "(`D-CAT-05`)."
        ),
    )
    nombre = models.CharField(max_length=160, verbose_name="Nombre")
    estado = models.CharField(
        max_length=16,
        choices=EstadoEquipo.choices,
        default=EstadoEquipo.ACTIVO,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "fest_equipo"
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["inscripcion_id", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion", "disciplina"],
                name="fest_equipo_disciplina_unica_por_inscripcion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.disciplina_id})"


__all__ = ["Equipo", "Inscripcion"]
