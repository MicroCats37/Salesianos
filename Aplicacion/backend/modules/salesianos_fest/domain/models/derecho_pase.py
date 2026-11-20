"""DERECHOS de entrada: la compra de un lote, sus beneficiarios y las cortesías.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Este archivo contiene las TRES piezas del agregado de pases y el acta de su
activación:

| Modelo | Qué es |
|---|---|
| `CompraPase` | El LOTE comprado: cuántos pases, a qué precio congelado y con qué token privado de gestión |
| `PaseBeneficiario` | El DERECHO efectivo de una persona: laENTRY que se puede validar |
| `CortesiaPase` | El ACTA auditada de una cortesía: actor, motivo y fecha, **sin** compra |
| `ActivacionPase` | El ACTA de la activación de derechos: la clave de idempotencia |

Invariantes congeladas:

- **Una compra pendiente NO habilita ningún derecho** (`RN-P02`, `QA-P01`):
  `CompraPase.estado` es `PENDIENTE` hasta que la ACTIVACIÓN de derechos
  (FND-05) lo cambia a `PAGADA`. Sólo entonces se puede asignar.
- **El comprador y el asistente pueden ser personas distintas** (`RN-P04`):
  `CompraPase.comprador` es el TITULAR de la compra; `PaseBeneficiario.
  persona` es el BENEFICIARIO del derecho.
- **Una cortesía NO es un cobro de S/ 0** (`RN-P05`): `CortesiaPase` no tiene
  NINGUNA columna que la pueda enlazar con una compra, una orden o una
  transacción. La ausencia de ese enlace ES la garantía.
- **Un derecho no se duplica** (`RN-P07`): la restricción parcial única
  `(edicion, pase, persona) WHERE estado = 'ACTIVO'` es la autoridad. Vale
  para los DOS orígenes: una cortesía no puede duplicar una compra, ni al
  revés.
- **La revocación es permanente y auditada** (`RN-P08`): el derecho revocado
  deja de ser canjeable para validaciones futuras; los consumos ya
  occurring permanecen.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6): campos, `Meta` y
`__str__`. La lógica vive en los servicios.
"""

from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from modules.salesianos_fest.domain.constants import (
    EstadoCompraPase,
    EstadoCortesiaPase,
    EstadoDerechoPase,
    OrigenDerechoPase,
)
from modules.salesianos_fest.domain.models.pase import Pase


class CompraPase(BaseModel):
    """El LOTE de pases comprado por una persona.

    Es el hecho COMERCIAL del dominio de pases. La compra de `commerce` es
    el hecho FINANCIERO: esta fila la REFERENCIA (`compra`), no la duplica
    (`RN-C08`, "regla transversal 4": un hecho financiero conserva su
    historia aunque se cancele un derecho derivado).
    """

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="compras_de_pases",
        verbose_name="Edición",
    )
    pase = models.ForeignKey(
        Pase,
        on_delete=models.PROTECT,
        related_name="compras",
        verbose_name="Pase",
    )
    comprador = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="compras_de_pases",
        verbose_name="Comprador",
        help_text=(
            "Persona que COMPRA. Puede no tener cuenta: la compra invitada no "
            "obliga a crear un `Usuario` (`FL-06` paso 2)."
        ),
    )
    contacto_email = models.EmailField(
        blank=True,
        default="",
        verbose_name="Correo de contacto",
        help_text=(
            "Correo que dejó el visitante. Es un contacto, NO un activador del "
            "derecho: el correo no habilita nada (`contratos/02` §5)."
        ),
    )
    compra = models.OneToOneField(
        "commerce.Compra",
        on_delete=models.PROTECT,
        related_name="compra_de_pases",
        null=True,
        blank=True,
        verbose_name="Compra",
        help_text=(
            "Compra de `commerce` que financia este lote. Es la MISMA compra "
            "que crea el flujo: no se duplica el hecho financiero."
        ),
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad de pases",
    )
    asignados = models.PositiveIntegerField(
        default=0,
        verbose_name="Pases asignados",
        help_text=(
            "Unidades del lote ya otorgadas. Lo mueve el servicio de "
            "capacidad con una sentencia ATÓMICA CONDICIONAL: dos "
            "asignaciones simultáneas NO pueden sobre-asignar el lote. "
            "La revocación NO lo decrementa: un derecho revocado sigue "
            "ocupando su unidad (`FR-05` §2.3)."
        ),
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio unitario",
        help_text=(
            "Precio CONGELADO por el servidor contra el catálogo vigente "
            "(`RN-C02`). El cliente no impone un importe."
        ),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Total",
        help_text="Total congelado: cantidad × precio unitario.",
    )
    moneda = models.CharField(
        max_length=3,
        default="PEN",
        verbose_name="Moneda",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoCompraPase.choices,
        default=EstadoCompraPase.PENDIENTE,
        verbose_name="Estado",
        help_text=(
            "`PENDIENTE` no habilita ningún derecho. Lo cambia la ACTIVACIÓN "
            "de derechos cuando el pago está confirmado (`RN-P02`)."
        ),
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token privado de gestión",
        help_text=(
            "Credencial del enlace privado de gestión (`/pases/gestionar/"
            "[token]`). Es de ÁMBITO POR COMPRA: sólo abre ESTA compra. "
            "Nunca se publica en un listado ni se acepta por DNI."
        ),
    )
    token_expira_en = models.DateTimeField(
        verbose_name="El token expira en",
        help_text=(
            "Vencimiento del enlace. La POLÍTICA exacta sigue ABIERTA "
            "(`GOV-01-OPEN-05`); el MECANISMO está congelado."
        ),
    )
    token_revocado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Token revocado en",
        help_text="revocabilidad: el enlace puede invalidarse sin borrar el hecho.",
    )
    referencia = models.CharField(
        max_length=200,
        verbose_name="Referencia de la intención",
        help_text=(
            "Referencia ESTABLE de la intención de compra. La usa `commerce` "
            "para no duplicar la compra pendiente (`FR-04` I-4) y la lee el "
            "activador de derechos."
        ),
    )

    class Meta:
        db_table = "fest_compra_pase"
        verbose_name = "Compra de pases"
        verbose_name_plural = "Compras de pases"
        ordering = ["-created_at"]
        constraints = [
            # Una persona NO tiene dos lotes PENDIENTES de la misma
            # intención: reintentar recupera el existente en vez de
            # duplicarlo (FR-04 I-4).
            models.UniqueConstraint(
                fields=["comprador", "edicion", "pase", "referencia"],
                condition=models.Q(estado=EstadoCompraPase.PENDIENTE),
                name="fest_compra_pase_pendiente_unica_por_intencion",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="fest_compra_pase_total_no_negativo",
            ),
            # No se otorgan más pases de los comprados (`RN-P02`).
            models.CheckConstraint(
                condition=models.Q(asignados__lte=models.F("cantidad")),
                name="fest_compra_pase_asignados_no_superan_cantidad",
            ),
        ]
        indexes = [
            models.Index(
                fields=["edicion", "estado"],
                name="fest_compra_pase_ed_estado",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.pase_id} ({self.estado})"


class PaseBeneficiario(BaseModel):
    """El DERECHO efectivo de una persona para un tipo de pase.

    Es la fila que `validaciones` consultará (`FR-05` §5): dice quién puede
    ingresar, cuánto y en qué estado. NUNCA duplica un derecho: la
    restricción parcial única `(edicion, pase, persona) WHERE estado =
    'ACTIVO'` es la autoridad, y vale para los DOS orígenes.

    El ORIGEN dice de dónde viene el derecho (`RN-P02`):

    - `COMPRA` — lo financia una compra pagada (`compra_pase`).
    - `CORTESIA` — lo otorga un administrador con motivo (`cortesia`).
    """

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="derechos_de_pase",
        verbose_name="Edición",
    )
    pase = models.ForeignKey(
        Pase,
        on_delete=models.PROTECT,
        related_name="beneficiarios",
        verbose_name="Pase",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="derechos_de_pase",
        verbose_name="Beneficiario",
        help_text="La persona que ASISTE. Puede no ser la compradora (`RN-P04`).",
    )
    origen = models.CharField(
        max_length=16,
        choices=OrigenDerechoPase.choices,
        verbose_name="Origen del derecho",
    )
    compra_pase = models.ForeignKey(
        CompraPase,
        on_delete=models.PROTECT,
        related_name="beneficiarios",
        null=True,
        blank=True,
        verbose_name="Compra de pases",
    )
    cortesia = models.ForeignKey(
        "CortesiaPase",
        on_delete=models.PROTECT,
        related_name="derechos",
        null=True,
        blank=True,
        verbose_name="Cortesía",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoDerechoPase.choices,
        default=EstadoDerechoPase.ACTIVO,
        verbose_name="Estado",
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad",
        help_text="Unidades de entrada que concede este derecho.",
    )
    cantidad_consumida = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad consumida",
        help_text=(
            "Unidades ya canjeadas. La escribe el módulo que valida "
            "(`XCT-01`); aquí nace en cero."
        ),
    )
    actor_usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="derechos_de_pase_otorgados",
        null=True,
        blank=True,
        verbose_name="Actor (cuenta)",
    )
    actor_persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="derechos_de_pase_otorgados",
        null=True,
        blank=True,
        verbose_name="Actor (persona)",
    )
    motivo = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo",
        help_text=(
            "Motivo del otorgamiento. Es OBLIGATORIO en la cortesía "
            "(`RN-P05`) y opcional en la asignación de una compra."
        ),
    )
    asignado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Asignado en",
    )
    revocado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Revocado en",
    )
    motivo_revocacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo de la revocación",
    )

    class Meta:
        db_table = "fest_pase_beneficiario"
        verbose_name = "Beneficiario de pase"
        verbose_name_plural = "Beneficiarios de pase"
        ordering = ["-asignado_en"]
        constraints = [
            # Una persona NO tiene dos derechos ACTIVOS del mismo tipo de pase
            # en la misma edición. La restricción vale para los DOS orígenes:
            # una cortesía no puede duplicar una compra (`RN-P07`).
            models.UniqueConstraint(
                fields=["edicion", "pase", "persona"],
                condition=models.Q(estado=EstadoDerechoPase.ACTIVO),
                name="fest_pase_beneficiario_activo_unico_por_persona",
            ),
            # Dentro de una MISMA compra, una persona se asigna UNA sola vez.
            models.UniqueConstraint(
                fields=["compra_pase", "persona"],
                name="fest_pase_beneficiario_unico_por_compra_y_persona",
            ),
            # El origen y su soporte van juntos: o compra, o cortesía.
            models.CheckConstraint(
                condition=(
                    models.Q(
                        origen=OrigenDerechoPase.COMPRA,
                        compra_pase__isnull=False,
                        cortesia__isnull=True,
                    )
                    | models.Q(
                        origen=OrigenDerechoPase.CORTESIA,
                        compra_pase__isnull=True,
                        cortesia__isnull=False,
                    )
                ),
                name="fest_pase_beneficiario_origen_coherente",
            ),
            # No se consume más de lo que se concedió (`RN-P07`).
            models.CheckConstraint(
                condition=models.Q(cantidad_consumida__lte=models.F("cantidad")),
                name="fest_pase_beneficiario_consumido_no_supera_cantidad",
            ),
        ]
        indexes = [
            models.Index(
                fields=["edicion", "estado"],
                name="fest_pase_benef_edicion_estado",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.persona_id} → {self.pase_id} ({self.estado})"


class CortesiaPase(BaseModel):
    """El ACTA auditada de una cortesía: un derecho gratuito y su motivo.

    `FL-07` paso 3: **nunca** crea orden ni transacción de pago. Este modelo
    NO tiene ninguna columna que lo enlace con `commerce.Compra`, con
    `pagos.OrdenPago` ni con `pagos.TransaccionPago`: la ausencia del
    enlace es la garantía estructural de `RN-P05`.

    `FL-07` paso 2: el backend registra el derecho gratuito CON AUDITORÍA.
    Por eso el ACTOR y el MOTIVO son obligatorios.
    """

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="cortesias_de_pase",
        verbose_name="Edición",
    )
    pase = models.ForeignKey(
        Pase,
        on_delete=models.PROTECT,
        related_name="cortesias",
        verbose_name="Pase",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="cortesias_de_pase",
        verbose_name="Beneficiario",
    )
    actor_usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="cortesias_de_pase_otorgadas",
        null=True,
        blank=True,
        verbose_name="Actor (cuenta)",
    )
    actor_persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="cortesias_de_pase_otorgadas",
        null=True,
        blank=True,
        verbose_name="Actor (persona)",
    )
    motivo = models.TextField(
        verbose_name="Motivo",
        help_text=(
            "Motivo del otorgamiento. OBLIGATORIO (`RN-P05`): una cortesía sin "
            "motivo no se registra."
        ),
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoCortesiaPase.choices,
        default=EstadoCortesiaPase.ACTIVA,
        verbose_name="Estado",
    )
    concedido_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Concedido en",
    )
    revocado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Revocado en",
    )
    motivo_revocacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo de la revocación",
    )

    class Meta:
        db_table = "fest_cortesia_pase"
        verbose_name = "Cortesía de pase"
        verbose_name_plural = "Cortesías de pase"
        ordering = ["-concedido_en"]
        constraints = [
            # Una cortesía tiene SIEMPRE un actor: sin actor no hay
            # auditoría (`RN-P05`).
            models.CheckConstraint(
                condition=(
                    models.Q(actor_usuario__isnull=False)
                    | models.Q(actor_persona__isnull=False)
                ),
                name="fest_cortesia_pase_actor_obligatorio",
            ),
        ]
        indexes = [
            models.Index(
                fields=["edicion", "estado"],
                name="fest_cortesia_pase_ed_estado",
            ),
        ]

    def __str__(self) -> str:
        return f"Cortesía {self.pase_id} → {self.persona_id} ({self.estado})"


class ActivacionPase(BaseModel):
    """El acta de una activación de derechos de pases.

    Es el hecho que hace la activación idempotente: su `clave` es ÚNICA y
    la produce el coordinador de `commerce` (`FR-04` I-2). Un reintento de
    la MISMA compra no vuelve a habilitar los pases (`QA-P01`).
    """

    compra_pase = models.ForeignKey(
        CompraPase,
        on_delete=models.PROTECT,
        related_name="activaciones",
        verbose_name="Compra de pases",
    )
    clave = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="Clave de activación",
        help_text=(
            "Clave de idempotencia ESTABLE que produce el coordinador de "
            "`commerce`. Es ÚNICA: es la autoridad del «exactamente una vez»."
        ),
    )
    compra_id = models.UUIDField(
        verbose_name="Compra de commerce",
        help_text="Identificador de la compra de `commerce` que financió el lote.",
    )
    cantidad = models.PositiveIntegerField(
        default=0,
        verbose_name="Pases habilitados",
    )
    aplicada_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Aplicada en",
    )

    class Meta:
        db_table = "fest_activacion_pase"
        verbose_name = "Activación de pases"
        verbose_name_plural = "Activaciones de pases"
        ordering = ["-aplicada_en"]
        indexes = [
            models.Index(
                fields=["compra_pase"],
                name="fest_activacion_pase_compra",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} pases ({self.compra_pase_id})"


__all__ = [
    "ActivacionPase",
    "CompraPase",
    "CortesiaPase",
    "PaseBeneficiario",
]
