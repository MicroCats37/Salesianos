"""Modelo directo del torneo de `mit/SALESIANOS`."""

from django.db import models


class GrupoTorneo(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.CASCADE,
        related_name="grupos_torneo",
    )
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "competencia_grupos_torneo"
        ordering = ["id"]


class EquipoTorneo(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    equipo = models.ForeignKey(
        "salesianos_fest.Equipo",
        on_delete=models.PROTECT,
        related_name="participaciones_torneo",
        null=True,
        blank=True,
    )
    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.CASCADE,
        related_name="equipos_torneo",
    )
    grupo = models.ForeignKey(
        GrupoTorneo,
        on_delete=models.PROTECT,
        related_name="equipos",
    )

    class Meta:
        db_table = "competencia_equipos_torneo"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["competencia", "equipo"],
                condition=models.Q(equipo__isnull=False),
                name="competencia_torneo_equipo_unico",
            )
        ]


class PartidoTorneo(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.CASCADE,
        related_name="partidos_torneo",
    )
    grupo = models.ForeignKey(
        GrupoTorneo,
        on_delete=models.PROTECT,
        related_name="partidos",
        null=True,
        blank=True,
    )
    etapa = models.CharField(max_length=16)
    posicion = models.PositiveIntegerField(default=0)
    local = models.ForeignKey(
        EquipoTorneo,
        on_delete=models.PROTECT,
        related_name="partidos_local",
        null=True,
        blank=True,
    )
    visitante = models.ForeignKey(
        EquipoTorneo,
        on_delete=models.PROTECT,
        related_name="partidos_visitante",
        null=True,
        blank=True,
    )
    programado_en = models.DateTimeField(null=True, blank=True)
    cancha = models.CharField(max_length=30, null=True, blank=True)
    duracion_minutos = models.PositiveIntegerField(default=30)
    estado = models.CharField(max_length=16, default="scheduled")
    puntaje_local = models.PositiveIntegerField(null=True, blank=True)
    puntaje_visitante = models.PositiveIntegerField(null=True, blank=True)
    penales_local = models.PositiveIntegerField(null=True, blank=True)
    penales_visitante = models.PositiveIntegerField(null=True, blank=True)
    ganador = models.ForeignKey(
        EquipoTorneo,
        on_delete=models.PROTECT,
        related_name="partidos_ganados",
        null=True,
        blank=True,
    )
    decision = models.CharField(max_length=20, null=True, blank=True)
    segundos_transcurridos = models.PositiveIntegerField(default=0)
    ejecutando_desde = models.DateTimeField(null=True, blank=True)
    segmento = models.CharField(max_length=20, default="regular")

    class Meta:
        db_table = "competencia_partidos_torneo"
        ordering = ["programado_en", "id"]


__all__ = ["EquipoTorneo", "GrupoTorneo", "PartidoTorneo"]
