"""La CREDENCIAL (`Ticket`) y el ACTA de validación (`ValidacionTicket`).

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §1, §2, §3

- `Ticket` es la CREDENCIAL que el operador escanea o teclea. REFERENCIA un
  derecho existente: no lo duplica.
- `ValidacionTicket` es el ACTA de cada intento: actor, instante, operación,
  cantidad y resultado.

**EL TICKET NO ES EL DERECHO** (`FR-05` §1, prohibición 2). Es una credencial
que apunta al derecho que vive en su módulo dueño: `PaseBeneficiario` en
`salesianos_fest`, `Pedido` en `marketplace`. Por eso NO tiene cantidades
propias: las publica el dueño.

**EL ACTA NO SE BORRA** (`RN-P07`, `RN-P08`). Un intento denegado también
queda registrado: el operador necesita saber qué se intentó, y el historial
conserva los consumos ya ocurridos.

**LA CLAVE DE IDEMPOTENCIA** identifica UNA intención (`FR-04` §2.2): una
repetición devuelve el resultado de la primera ejecución, y reutilizar la
clave con otra operación es un error del cliente.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6): campos, `Meta` y
`__str__`. La lógica vive en los servicios.
"""

from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from modules.validaciones.domain.constants import (
    EstadoTicketChoices,
    OperacionValidacionChoices,
    ResultadoValidacionChoices,
    TipoDerechoChoices,
)


class Ticket(BaseModel):
    """La CREDENCIAL que el operador escanea o teclea.

    Es una REFERENCIA a un derecho que ya existe en su módulo dueño: no lo
    duplica, no lo otorga y no lo modifica (`FR-05` §1). Por eso NO tiene
    cantidades propias: las publica el dueño.

    El `codigo` es la credencial. Es un SECRETO: no se publica en listados,
    no se registra en la auditoría y no se enseña en pantalla para que otro
    lo use.
    """

    codigo = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Código de la credencial",
        help_text=(
            "Credencial que el operador escanea o teclea. Es un secreto: no "
            "aparece en ningún listado ni en la auditoría."
        ),
    )
    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Edición",
    )
    tipo_derecho = models.CharField(
        max_length=24,
        choices=TipoDerechoChoices.choices,
        verbose_name="Tipo de derecho",
        help_text="El discriminante del módulo dueño del derecho.",
    )
    operacion = models.CharField(
        max_length=16,
        choices=OperacionValidacionChoices.choices,
        verbose_name="Operación",
        help_text="La operación que ejecuta el operador: ingreso o entrega.",
    )
    pase_beneficiario = models.ForeignKey(
        "salesianos_fest.PaseBeneficiario",
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
        verbose_name="Derecho de pase",
    )
    pedido = models.ForeignKey(
        "marketplace.Pedido",
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
        verbose_name="Pedido",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoTicketChoices.choices,
        default=EstadoTicketChoices.VIGENTE,
        verbose_name="Estado de la credencial",
    )
    emitido_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Emitido en",
    )

    class Meta:
        db_table = "validaciones_ticket"
        verbose_name = "Ticket de validación"
        verbose_name_plural = "Tickets de validación"
        ordering = ["-emitido_en"]
        constraints = [
            # La credencial apunta a UN derecho y a UNA operación, y la
            # operación se deriva del tipo de derecho: un ticket de entrega
            # no puede apuntar a un pase (`FR-05` §1).
            models.CheckConstraint(
                condition=(
                    models.Q(
                        tipo_derecho__in=[
                            TipoDerechoChoices.PASE,
                            TipoDerechoChoices.ENTRADA_CORTESIA,
                        ],
                        operacion=OperacionValidacionChoices.INGRESO,
                        pase_beneficiario__isnull=False,
                        pedido__isnull=True,
                    )
                    | models.Q(
                        tipo_derecho=TipoDerechoChoices.PRODUCTO,
                        operacion=OperacionValidacionChoices.ENTREGA,
                        pase_beneficiario__isnull=True,
                        pedido__isnull=False,
                    )
                ),
                name="validaciones_ticket_referencia_coherente",
            ),
        ]
        indexes = [
            models.Index(
                fields=["edicion", "tipo_derecho"],
                name="validaciones_ticket_ed_tipo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tipo_derecho} ({self.estado})"


class ValidacionTicket(BaseModel):
    """El ACTA de un intento de validación.

    Guarda QUIÉN, CUÁNDO, QUÉ operación, CUÁNTA cantidad y con QUÉ resultado
    (`FR-05` §2.2). Un intento DENEGADO también se registra: el operador
    necesita saber qué se intentó, y el historial conserva lo que ya ocurrió
    (`RN-P07`, `RN-P08`).

    El ACTOR es obligatorio: una validación sin actor no es auditable.

    `idempotency_key` identifica UNA intención. Es ÚNICA cuando existe: una
    repetición devuelve el resultado de la primera ejecución y reutilizar la
    clave con otra operación es un error del cliente (`FR-04` §2.2).

    `huella` es la huella de la INTENCIÓN (código + cantidad). Sirve para
    distinguir una repetición fiel de un reusing con otra carga.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,
        related_name="validaciones",
        verbose_name="Ticket",
    )
    operacion = models.CharField(
        max_length=16,
        choices=OperacionValidacionChoices.choices,
        verbose_name="Operación",
    )
    resultado = models.CharField(
        max_length=16,
        choices=ResultadoValidacionChoices.choices,
        verbose_name="Resultado",
    )
    actor_usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="validaciones_de_ticket",
        null=True,
        blank=True,
        verbose_name="Actor (cuenta)",
    )
    actor_persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="validaciones_de_ticket",
        null=True,
        blank=True,
        verbose_name="Actor (persona)",
    )
    cantidad = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Cantidad consumida",
        help_text="Unidades consumidas. Un intento denegado consume CERO.",
    )
    cantidad_restante = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Cantidad restante",
        help_text=(
            "Unidades que quedaban disponibles DESPUÉS del consumo, según el "
            "módulo dueño. Se guarda para que la repetición idempotente "
            "devuelva el mismo dato que la primera ejecución."
        ),
    )
    motivo_codigo = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Código del motivo",
        help_text="Código estable del motivo. Vacío cuando el resultado es permitido.",
    )
    motivo_mensaje = models.CharField(
        max_length=240,
        blank=True,
        default="",
        verbose_name="Mensaje del motivo",
        help_text="Prosa pública segura. Nunca interpola identificadores.",
    )
    idempotency_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        unique=True,
        verbose_name="Clave de idempotencia",
    )
    huella = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Huella de la intención",
        help_text="Huella del código y la cantidad confirmados.",
    )
    registrado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registrado en",
    )

    class Meta:
        db_table = "validaciones_acta"
        verbose_name = "Validación de ticket"
        verbose_name_plural = "Validaciones de ticket"
        ordering = ["-registrado_en"]
        constraints = [
            # Sin actor no hay auditoría (`RN-P07`).
            models.CheckConstraint(
                condition=(
                    models.Q(actor_usuario__isnull=False)
                    | models.Q(actor_persona__isnull=False)
                ),
                name="validaciones_acta_actor_obligatorio",
            ),
            # Un permiso consume unidades; un rechazo no consume ninguna.
            models.CheckConstraint(
                condition=(
                    models.Q(
                        resultado=ResultadoValidacionChoices.PERMITIDO,
                        cantidad__gte=1,
                    )
                    | models.Q(
                        resultado=ResultadoValidacionChoices.DENEGADO,
                        cantidad=0,
                    )
                ),
                name="validaciones_acta_cantidad_coherente",
            ),
        ]
        indexes = [
            models.Index(
                fields=["ticket", "resultado"],
                name="validaciones_acta_ticket_res",
            ),
            models.Index(
                fields=["actor_usuario", "registrado_en"],
                name="validaciones_acta_actor_fecha",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.operacion} {self.resultado} ({self.cantidad})"


__all__ = [
    "Ticket",
    "ValidacionTicket",
]
