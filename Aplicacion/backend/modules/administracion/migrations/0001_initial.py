"""Migración inicial del módulo `administracion` (el ACTA transversal).

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El módulo no tiene modelos de dominio: el único modelo propio es el ACTA de
las acciones sensibles (`AccionAuditada`).
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Crea el ACTA transversal de la administración."""

    initial = True

    dependencies = [
        ("eventos", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccionAuditada",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Fecha de creación",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Última actualización",
                    ),
                ),
                (
                    "actor_nombre",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=160,
                        verbose_name="Actor (nombre)",
                        help_text="La FOTO del actor en el momento de la acción.",
                    ),
                ),
                (
                    "accion",
                    models.CharField(
                        max_length=64,
                        verbose_name="Acción",
                        help_text="El código estable de la acción.",
                    ),
                ),
                (
                    "entidad",
                    models.CharField(
                        max_length=64,
                        verbose_name="Entidad",
                        help_text="El tipo de la entidad afectada.",
                    ),
                ),
                (
                    "entidad_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=64,
                        verbose_name="Entidad (identificador)",
                    ),
                ),
                (
                    "motivo",
                    models.TextField(
                        verbose_name="Motivo",
                        help_text=(
                            "POR QUÉ se ejecutó la acción. Es OBLIGATORIO en las "
                            "acciones sensibles: un comando sin motivo no se ejecuta."
                        ),
                    ),
                ),
                (
                    "datos",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="Datos",
                        help_text=(
                            "El contexto auditable, ya SANITIZADO. El servicio de "
                            "auditoría es el único que escribe aquí y nunca guarda "
                            "claves prohibidas."
                        ),
                    ),
                ),
                (
                    "actor_usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="acciones_auditadas_admin",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Actor",
                        help_text=(
                            "La cuenta que ejecutó la acción. `SET_NULL`: el acta "
                            "NO se borra cuando la cuenta se da de baja, porque el "
                            "hecho ocurrió."
                        ),
                    ),
                ),
                (
                    "edicion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="acciones_auditadas",
                        to="eventos.edicion",
                        verbose_name="Edición",
                    ),
                ),
            ],
            options={
                "verbose_name": "Acción auditada",
                "verbose_name_plural": "Acciones auditadas",
                "db_table": "admin_accion_auditada",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="accionauditada",
            index=models.Index(
                fields=["edicion", "accion"],
                name="admin_accion_aud_ed_accion",
            ),
        ),
        migrations.AddIndex(
            model_name="accionauditada",
            index=models.Index(
                fields=["-created_at"],
                name="admin_accion_aud_fecha",
            ),
        ),
    ]
