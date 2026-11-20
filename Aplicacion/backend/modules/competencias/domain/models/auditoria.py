"""`AuditoriaOperacion` — el ACTA de cada operación protegida.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

`RN-K02`: "Encuentros tienen programación, participantes, resultado, vencedor,
estado y AUDITORÍA".

Este módulo registra su propia auditoría en una tabla explícita, en vez de
delegar en un historial automático:

- el ACTA es un HECHO de negocio: existe aunque el dato que audita cambie
  después (`RN-K02`, `QA-K03`). Un historial automático describe el estado;
  un acta describe la OPERACIÓN;
- la ACTA nunca se borra. Una corrección posterior no borra la corrección
  anterior: la deja como antecedente (`frontend/05` §3, "historial de
  correcciones");
- el `detalle` guarda el antes/después de la operación. Es contexto técnico
  del servidor: NUNCA se publica en una respuesta HTTP.

El `actor` es la cuenta que ejecutó la operación. Es opcional porque una
operación puede ejecutarse desde un proceso (una migración, un comando) sin
un actor autenticado.
"""

from django.db import models

from core.models import BaseModel


class AccionAuditada(models.TextChoices):
    """Vocabulary of the audited operations of the module."""

    CREACION_COMPETENCIA = "CREACION_COMPETENCIA", "Creación de competencia"
    INCORPORACION_EQUIPO = "INCORPORACION_EQUIPO", "Incorporación de equipo"
    EDICION_EQUIPO = "EDICION_EQUIPO", "Edición de equipo"
    CREACION_RONDA = "CREACION_RONDA", "Creación de ronda"
    CREACION_ENCUENTRO = "CREACION_ENCUENTRO", "Creación de encuentro"
    PARTICIPANTES = "PARTICIPANTES", "Cambio de participantes"
    ENLACE = "ENLACE", "Cambio de enlace"
    PROGRAMACION = "PROGRAMACION", "Programación de horario"
    BYE = "BYE", "Asignación de bye"
    ESTADO = "ESTADO", "Cambio de estado del encuentro"
    CANCELACION = "CANCELACION", "Cancelación de encuentro"
    RESULTADO = "RESULTADO", "Registro de resultado"
    AVANCE = "AVANCE", "Avance confirmado"
    CORRECCION = "CORRECCION", "Corrección de resultado"


class AuditoriaOperacion(BaseModel):
    """El acta de una operación protegida."""

    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.PROTECT,
        related_name="auditorias",
        null=True,
        blank=True,
        verbose_name="Competencia",
    )
    encuentro = models.ForeignKey(
        "competencias.Encuentro",
        on_delete=models.PROTECT,
        related_name="auditorias",
        null=True,
        blank=True,
        verbose_name="Encuentro",
    )
    accion = models.CharField(
        max_length=40,
        choices=AccionAuditada.choices,
        verbose_name="Acción",
    )
    actor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="auditorias_competencias",
        null=True,
        blank=True,
        verbose_name="Actor",
        help_text="Cuenta que ejecutó la operación. Vacío si no hubo actor autenticado.",
    )
    motivo = models.TextField(
        verbose_name="Motivo",
        help_text="Motivo auditado de la operación (5..500 caracteres).",
    )
    detalle = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Detalle",
        help_text=(
            "Antes/después de la operación. Contexto TÉCNICO del servidor: "
            "nunca se publica en una respuesta HTTP."
        ),
    )

    class Meta:
        db_table = "competencia_auditoria"
        verbose_name = "Auditoría de operación"
        verbose_name_plural = "Auditorías de operaciones"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["encuentro", "-created_at"],
                name="ix_comp_aud_enc_created",
            ),
            models.Index(
                fields=["competencia", "-created_at"],
                name="ix_comp_aud_comp_created",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.accion} ({self.encuentro_id or self.competencia_id})"


__all__ = ["AccionAuditada", "AuditoriaOperacion"]
