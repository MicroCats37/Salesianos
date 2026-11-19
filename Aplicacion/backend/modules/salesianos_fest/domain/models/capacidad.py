"""La CAPACIDAD pagada de una inscripción y los beneficios concedidos.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Invariantes:

- **La capacidad pagada sólo crece cuando los DERECHOS se activan**
  (`RN-I02`): una compra pendiente no habilita ningún cupo. El incremento lo
  hace el ACTIVADOR de este módulo, a través del puerto congelado
  `IActivadorDominioCompra` de FND-05, cuando el pago está confirmado.
- **Una activación aplica la capacidad UNA sola vez** (`RN-I02`, `QA-I02`):
  la restricción única de `ActivacionCapacidad.clave` es la autoridad. La
  clave es la de FND-05 (`activacion:{origen}:{compra_id}`), que es ESTABLE
  entre reintentos, así que un reintento converge en el MISMO resultado y no
  vuelve a sumar cupos.
- **Un beneficio `FIJO_INICIAL` se concede UNA sola vez por inscripción**
  (`RN-I06`): la restricción única `(inscripcion, beneficio)` lo garantiza en
  la base de datos, no en una comprobación de aplicación. Una AMPLIACIÓN no
  vuelve a concederlo.
- **Los beneficios `POR_CUPO` NO se conceden todavía**: su regla de reparto
  por tipo sigue ABIERTA (`PD-09`). El módulo DECLARA el beneficio y deja la
  concesión explícitamente pendiente; no inventa una regla de negocio.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6).
"""

from django.db import models

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import TipoActivacionCapacidad


class ActivacionCapacidad(BaseModel):
    """Acta de una activación de capacidad sobre una inscripción.

    Es el hecho que hace la activación idempotente: una fila por CLAVE de
    activación. La clave la produce el coordinador de `commerce` y es estable
    entre reintentos, así que el segundo intento de la MISMA compra NO vuelve
    a sumar cupos.
    """

    inscripcion = models.ForeignKey(
        "salesianos_fest.Inscripcion",
        on_delete=models.PROTECT,
        related_name="activaciones_capacidad",
        verbose_name="Inscripción",
    )
    clave = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="Clave de activación",
        help_text=(
            "Clave de idempotencia de la activación. La produce el "
            "coordinador de `commerce` y es estable entre reintentos."
        ),
    )
    compra_id = models.UUIDField(
        verbose_name="Compra de origen",
        help_text=(
            "Identificador de la compra que financia la capacidad. Se guarda "
            "como dato, no como clave foránea: la compra es de `commerce`, "
            "que es su dueño."
        ),
    )
    tipo = models.CharField(
        max_length=16,
        choices=TipoActivacionCapacidad.choices,
        verbose_name="Tipo",
        help_text=(
            "`INICIAL` es la activación del alta; `EXPANSION` es la de una "
            "compra de cupos extra."
        ),
    )
    cupos = models.PositiveIntegerField(
        verbose_name="Cupos habilitados",
        help_text="Cupos que esta activación sumó a la capacidad pagada.",
    )
    aplicada_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Aplicada en",
    )

    class Meta:
        db_table = "fest_activacion_capacidad"
        verbose_name = "Activación de capacidad"
        verbose_name_plural = "Activaciones de capacidad"
        ordering = ["-aplicada_en"]
        indexes = [
            models.Index(
                fields=["inscripcion", "tipo"],
                name="fest_activacion_insc_tipo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tipo} (+{self.cupos}) {self.inscripcion_id}"


class BeneficioConcedido(BaseModel):
    """La concesión efectiva de un beneficio de paquete a una inscripción.

    `PaqueteBeneficio` DECLARA lo que el paquete ofrece (`RN-P01`); este
    modelo registra lo que se CONCEDIÓ. La concesión es un hecho posterior,
    ligado al pago (`DOM-02`).
    """

    inscripcion = models.ForeignKey(
        "salesianos_fest.Inscripcion",
        on_delete=models.PROTECT,
        related_name="beneficios_concedidos",
        verbose_name="Inscripción",
    )
    beneficio = models.ForeignKey(
        "salesianos_fest.PaqueteBeneficio",
        on_delete=models.PROTECT,
        related_name="concesiones",
        verbose_name="Beneficio",
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad",
    )
    activacion = models.ForeignKey(
        "salesianos_fest.ActivacionCapacidad",
        on_delete=models.PROTECT,
        related_name="beneficios",
        verbose_name="Activación",
        help_text="La activación que concedió el beneficio.",
    )
    concedido_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Concedido en",
    )

    class Meta:
        db_table = "fest_beneficio_concedido"
        verbose_name = "Beneficio concedido"
        verbose_name_plural = "Beneficios concedidos"
        ordering = ["beneficio_id"]
        constraints = [
            # Un beneficio se concede UNA sola vez por inscripción (`RN-I06`).
            # Para los beneficios `POR_CUPO` —cuya regla sigue ABIERTA
            # (`PD-09`)— esta misma fila acumulará la cantidad cuando la
            # regla se cierre.
            models.UniqueConstraint(
                fields=["inscripcion", "beneficio"],
                name="fest_beneficio_concedido_unico_por_inscripcion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.beneficio_id} en {self.inscripcion_id} x{self.cantidad}"


__all__ = ["ActivacionCapacidad", "BeneficioConcedido"]
