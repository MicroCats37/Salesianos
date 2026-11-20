"""`AccionAuditada` — el ACTA de las acciones sensibles de la administración.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Un ACTA es el registro INMUTABLE de que una acción sensible ocurrió, con
**quién** la ejecutó, **cuándo** y **por qué** (`contratos/02` §6).

Este módulo declara el primer acta TRANSVERSAL: hasta ahora cada dominio
audita lo suyo (`CortesiaPase` es el acta de una cortesía, `ActivacionPase` el
acta de una activación). El acta transversal no sustituye a ninguna: se
escribe AL LADO del acta del dominio.

El acta NO guarda credenciales, tokens, cookies, cuerpos crudos de proveedor,
trazas, SQL ni rutas: son secretos o interiores. El `presenter` publica una
LISTA BLANCA del contexto, nunca el contenido crudo.

Los modelos son planos y anémicos (`contract/django-app-architecture-contract.md`
§4.2).
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class AccionAuditada(BaseModel):
    """El acta de una acción sensible ejecutada por un administrador."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="acciones_auditadas",
        null=True,
        blank=True,
        verbose_name="Edición",
    )
    actor_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="acciones_auditadas_admin",
        null=True,
        blank=True,
        verbose_name="Actor",
        help_text=(
            "La cuenta que ejecutó la acción. `SET_NULL`: el acta NO se "
            "borra cuando la cuenta se da de baja, porque el hecho ocurrió."
        ),
    )
    actor_nombre = models.CharField(
        max_length=160,
        blank=True,
        default="",
        verbose_name="Actor (nombre)",
        help_text="La FOTO del actor en el momento de la acción.",
    )
    accion = models.CharField(
        max_length=64,
        verbose_name="Acción",
        help_text="El código estable de la acción.",
    )
    entidad = models.CharField(
        max_length=64,
        verbose_name="Entidad",
        help_text="El tipo de la entidad afectada.",
    )
    entidad_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Entidad (identificador)",
    )
    motivo = models.TextField(
        verbose_name="Motivo",
        help_text=(
            "POR QUÉ se ejecutó la acción. Es OBLIGATORIO en las acciones "
            "sensibles: un comando sin motivo no se ejecuta."
        ),
    )
    datos = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos",
        help_text=(
            "El contexto auditable, ya SANITIZADO. El servicio de auditoría "
            "es el único que escribe aquí y nunca guarda claves prohibidas."
        ),
    )

    class Meta:
        db_table = "admin_accion_auditada"
        verbose_name = "Acción auditada"
        verbose_name_plural = "Acciones auditadas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["edicion", "accion"],
                name="admin_accion_aud_ed_accion",
            ),
            models.Index(
                fields=["-created_at"],
                name="admin_accion_aud_fecha",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.accion} por {self.actor_nombre or 'sistema'}"


__all__ = ["AccionAuditada"]
