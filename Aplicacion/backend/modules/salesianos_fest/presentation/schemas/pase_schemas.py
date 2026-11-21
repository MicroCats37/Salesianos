"""Contrato HTTP de los PASES, los beneficiarios y las cortesías.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques)

Ledger: `RT-PS-01`…`RT-PS-08` (provisionales, `SH-05` §1.4) · `RT-CM-02`
(congelado, `FR-07` §3.3) · `RT-RT-03` (congelado, `FR-07` §3.3).

Los wrappers se COMPONEN con los tres bloques conceptuales:

- **Identidad** — identificador y marcas de tiempo.
- **General** — la familia a la que pertenece (la edición) y el dinero.
- **Específico** — lo propio de cada caso de uso.

No hay `z.any()`, ni campos genéricos, ni campos de otros dominios.

**El payload de la compra NO admite importe**: el precio lo resuelve el
servidor contra el catálogo vigente (`RN-C02`). La cantidad NO lleva rango
en el schema: el límite de dominio lo declara y lo hace cumplir el módulo,
que responde con el código estable `CANTIDAD_INVALIDA` (422) del ledger.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


# ── Bloques del pase ────────────────────────────────────────────────────────


class PrecioPaseOut(BaseSchema):
    """Bloque general del precio de catálogo de un pase."""

    monto: Decimal = Field(..., ge=0, description="Monto del catálogo.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    vigente_desde: date = Field(..., description="Inicio de la vigencia.")
    vigente_hasta: date | None = Field(
        default=None,
        description="Fin de la vigencia. Vacío significa vigencia abierta.",
    )


class PaseIdentidadOut(BaseSchema):
    """Bloque de identidad de un pase."""

    id: UUID = Field(..., description="Identificador del pase.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class PaseGeneralOut(BaseSchema):
    """Bloque general de un pase: la edición a la que pertenece."""

    edicion_id: UUID = Field(..., description="Edición del pase.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")


class PaseEspecificoOut(BaseSchema):
    """Bloque específico de un pase."""

    nombre: str = Field(..., description="Nombre del pase.")
    slug: str = Field(..., description="Identificador del pase.")
    descripcion: str = Field(default="", description="Descripción del pase.")
    estado: str = Field(..., description="Estado del pase.")


class PaseOut(
    PaseIdentidadOut,
    PaseGeneralOut,
    PaseEspecificoOut,
):
    """Salida de un pase del catálogo."""

    precio: PrecioPaseOut = Field(..., description="Precio vigente del pase.")


class PaseDetalleOut(PaseIdentidadOut, PaseGeneralOut, PaseEspecificoOut):
    """Salida del detalle de un pase.

    `precio` es `NULL` cuando el pase NO tiene precio vigente: no hay
    precio de reserva inventado (`FL-01` paso 3).
    """

    precio: PrecioPaseOut | None = Field(
        default=None,
        description="Precio vigente. Vacío si el pase no está a la venta.",
    )


class PaseCatalogoOut(BaseSchema):
    """El catálogo de pases de UNA edición."""

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    pases: list[PaseOut] = Field(
        default_factory=list,
        description="Pases comprables de la edición.",
    )


# ── Compra ───────────────────────────────────────────────────────────────────


class ComprarPaseIn(BaseSchema):
    """El payload de la compra de pases.

    El comprador es una identidad CIVIL: puede no tener cuenta. El servidor
    la resuelve o la registra; **nunca** crea una cuenta (`FL-06` paso 2).
    """

    pase_id: UUID = Field(
        ...,
        description="Pase del catálogo que se compra.",
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description=(
            "Número de pases que se compran. El límite lo declara y lo hace "
            "cumplir el servidor (`CANTIDAD_INVALIDA`, 422)."
        ),
    )
    tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento del comprador.",
    )
    numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento del comprador.",
    )
    nombres: str = Field(
        ...,
        max_length=255,
        description="Nombres del comprador.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos del comprador.",
    )
    contacto_email: str = Field(
        default="",
        max_length=255,
        description=(
            "Correo de contacto. No habilita ningún derecho: es un contacto, "
            "no una credencial."
        ),
    )


class CompraPaseCreadaOut(BaseSchema):
    """Salida de la compra de un lote de pases.

    El token viaja AQUÍ y sólo aquí: es la credencial del enlace de gestión
    y no vuelve a aparecer en ningún listado.
    """

    compra_pase_id: UUID = Field(..., description="Lote de pases comprado.")
    compra_id: UUID = Field(..., description="Compra de `commerce` que lo financia.")
    orden_pago_id: UUID | None = Field(
        default=None,
        description="Orden de pago pendiente, si la hay.",
    )
    estado: str = Field(
        ...,
        description=(
            "Estado de la compra. `PENDIENTE` no habilita ningún pase: la "
            "asignación espera al pago confirmado."
        ),
    )
    pase_id: UUID = Field(..., description="Pase comprado.")
    pase_nombre: str = Field(..., description="Nombre del pase comprado.")
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    cantidad: int = Field(..., gt=0, description="Pases del lote.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio unitario congelado por el servidor.",
    )
    total: Decimal = Field(..., ge=0, description="Total congelado por el servidor.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    comprador_persona_id: UUID = Field(
        ...,
        description="Persona que compra. Puede no tener cuenta.",
    )
    comprador_nombres: str = Field(..., description="Nombres del comprador.")
    token: str = Field(
        ...,
        max_length=64,
        description=(
            "Token privado de gestión del enlace. Es de ÁMBITO POR COMPRA y "
            "viaja en la cabecera `X-Pase-Token`."
        ),
    )
    token_expira_en: datetime = Field(..., description="Vencimiento del enlace.")
    reutilizada: bool = Field(
        ...,
        description="Si la compra se recuperó en vez de crearse.",
    )
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta. La declara el dominio.",
    )


# ── Beneficiarios ───────────────────────────────────────────────────────────


class PaseBeneficiarioOut(BaseSchema):
    """Un derecho de entrada de una persona."""

    id: UUID = Field(..., description="Identificador del derecho.")
    pase_id: UUID = Field(..., description="Pase del derecho.")
    pase_nombre: str = Field(..., description="Nombre del pase.")
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    persona_id: UUID = Field(..., description="Persona que asiste.")
    persona_nombres: str = Field(..., description="Nombres de la persona.")
    persona_apellidos: str = Field(default="", description="Apellidos de la persona.")
    persona_tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    persona_numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento de la persona.",
    )
    origen: str = Field(
        ...,
        description="Origen del derecho: `COMPRA` o `CORTESIA`.",
    )
    estado: str = Field(..., description="Estado del derecho.")
    cantidad: int = Field(..., ge=1, description="Unidades que concede el derecho.")
    cantidad_consumida: int = Field(
        ...,
        ge=0,
        description="Unidades ya canjeadas.",
    )
    cantidad_disponible: int = Field(
        ...,
        ge=0,
        description="Unidades todavía canjeables.",
    )
    asignado_en: datetime = Field(..., description="Momento del otorgamiento.")
    motivo: str = Field(default="", description="Motivo del otorgamiento.")
    revocado_en: datetime | None = Field(
        default=None,
        description="Momento de la revocación, si la hubo.",
    )
    motivo_revocacion: str = Field(
        default="",
        description="Motivo de la revocación.",
    )


class PaseBeneficiariosOut(BaseSchema):
    """Los derechos de un lote de pases."""

    compra_pase_id: UUID = Field(..., description="Lote de pases.")
    estado: str = Field(..., description="Estado de la compra del lote.")
    cantidad: int = Field(..., ge=1, description="Pases del lote.")
    asignados: int = Field(
        ...,
        ge=0,
        description="Unidades ya otorgadas. La revocación no las devuelve.",
    )
    disponibles: int = Field(
        ...,
        ge=0,
        description="Unidades todavía por otorgar.",
    )
    beneficiarios: list[PaseBeneficiarioOut] = Field(
        default_factory=list,
        description="Derechos otorgados en el lote.",
    )


class PaseCompraDetalleOut(PaseBeneficiariosOut):
    """El detalle de la compra de un lote de pases.

    Es el mismo shape que el listado de beneficiarios más los datos
    comerciales del lote: el frontend consume una sola forma.
    """

    compra_id: UUID | None = Field(
        default=None,
        description="Compra de `commerce` que lo financia.",
    )
    orden_pago_id: UUID | None = Field(
        default=None,
        description="Orden de pago pendiente, si la hay.",
    )
    pase_id: UUID = Field(..., description="Pase comprado.")
    pase_nombre: str = Field(..., description="Nombre del pase comprado.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio unitario congelado.",
    )
    total: Decimal = Field(..., ge=0, description="Total congelado.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta. La declara el dominio.",
    )


class AsignarBeneficiarioIn(BaseSchema):
    """El payload de la asignación de un pase a una persona.

    La persona puede llegar por IDENTIFICADOR o por DOCUMENTO. La
    resolución y el registro de la identidad son de `usuarios`.
    """

    persona_id: UUID | None = Field(
        default=None,
        description="Persona del padrón, si ya se conoce.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=3,
        description="Tipo de documento del beneficiario.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento del beneficiario.",
    )
    nombres: str = Field(
        default="",
        max_length=255,
        description="Nombres del beneficiario si se resuelve por documento.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos del beneficiario si se resuelve por documento.",
    )
    motivo: str = Field(
        default="",
        max_length=500,
        description="Motivo de la asignación. Opcional en una compra.",
    )


class PaseBeneficiarioRevocadoOut(BaseSchema):
    """Salida de la revocación de un derecho de entrada."""

    compra_pase_id: UUID = Field(..., description="Lote de pases.")
    derecho_id: UUID = Field(..., description="Derecho revocado.")
    persona_id: UUID = Field(..., description="Persona del derecho.")
    estado: str = Field(..., description="Estado final del derecho.")
    revocado_en: datetime = Field(..., description="Momento de la revocación.")
    ya_revocado: bool = Field(
        ...,
        description=(
            "Si el derecho ya estaba revocado. La revocación es idempotente "
            "y esto NO es un error."
        ),
    )
    motivo: str = Field(default="", description="Motivo de la revocación.")


# ── Administración ───────────────────────────────────────────────────────────


class AdminPaseListItemOut(BaseSchema):
    """Una fila del listado administrativo de lotes de pases."""

    compra_pase_id: UUID = Field(..., description="Lote de pases.")
    estado: str = Field(..., description="Estado de la compra.")
    pase_id: UUID = Field(..., description="Pase del lote.")
    pase_nombre: str = Field(..., description="Nombre del pase.")
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    comprador_persona_id: UUID = Field(..., description="Persona que compró.")
    comprador_nombres: str = Field(..., description="Nombres del comprador.")
    cantidad: int = Field(..., ge=1, description="Pases del lote.")
    asignados: int = Field(..., ge=0, description="Unidades ya otorgadas.")
    total: Decimal = Field(..., ge=0, description="Total congelado.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    creado_en: datetime = Field(..., description="Momento de la compra.")


class AdminCortesiaListItemOut(BaseSchema):
    """Una fila del listado administrativo de cortesías."""

    id: UUID = Field(..., description="Acta de la cortesía.")
    derecho_id: UUID | None = Field(
        default=None,
        description=(
            "El DERECHO de entrada que creó la cortesía. La credencial de "
            "puerta se emite contra él. Es nulo sólo si el acta no tiene "
            "derecho: un identificador ausente nunca se inventa."
        ),
    )
    pase_nombre: str = Field(..., description="Nombre del pase otorgado.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    persona_nombres: str = Field(..., description="Nombres del beneficiario.")
    persona_tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento del beneficiario.",
    )
    persona_numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento del beneficiario.",
    )
    estado: str = Field(..., description="Estado de la cortesía.")
    motivo: str = Field(..., description="Motivo del otorgamiento.")
    actor_nombres: str = Field(default="", description="Nombres de quien otorgó.")
    concedido_en: datetime = Field(..., description="Momento del otorgamiento.")


class OtorgarCortesiaIn(BaseSchema):
    """El payload del otorgamiento de una cortesía.

    El MOTIVO es obligatorio (`RN-P05`). El ACTOR lo pone el servidor: es la
    cuenta autenticada que ejecuta la operación.
    """

    edicion_id: UUID = Field(
        ...,
        description="Edición del alcance de la cortesía.",
    )
    pase_id: UUID = Field(..., description="Pase que se otorga.")
    persona_id: UUID | None = Field(
        default=None,
        description="Persona del padrón, si ya se conoce.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento de la persona.",
    )
    nombres: str = Field(
        default="",
        max_length=255,
        description="Nombres de la persona si se resuelve por documento.",
    )
    apellidos: str = Field(
        default="",
        max_length=255,
        description="Apellidos de la persona si se resuelve por documento.",
    )
    motivo: str = Field(
        ...,
        max_length=500,
        description="Motivo del otorgamiento. Obligatorio.",
    )


class AdminCortesiaOut(BaseSchema):
    """Salida del otorgamiento de una cortesía."""

    id: UUID = Field(..., description="Acta de la cortesía.")
    derecho_id: UUID = Field(
        ...,
        description=(
            "El DERECHO de entrada que creó la cortesía. La credencial de "
            "puerta se emite contra él, y nace con el acta en la misma "
            "transacción."
        ),
    )
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    pase_id: UUID = Field(..., description="Pase otorgado.")
    pase_nombre: str = Field(..., description="Nombre del pase.")
    persona_id: UUID = Field(..., description="Persona que recibe la cortesía.")
    persona_nombres: str = Field(..., description="Nombres de la persona.")
    persona_tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    persona_numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento de la persona.",
    )
    estado: str = Field(..., description="Estado de la cortesía.")
    motivo: str = Field(..., description="Motivo del otorgamiento.")
    actor_usuario_id: UUID | None = Field(
        default=None,
        description="Cuenta que otorgó la cortesía.",
    )
    actor_nombres: str = Field(default="", description="Nombres de quien otorgó.")
    concedido_en: datetime = Field(..., description="Momento del otorgamiento.")
    revocado_en: datetime | None = Field(
        default=None,
        description="Momento de la revocación, si la hubo.",
    )


class RevocarCortesiaIn(BaseSchema):
    """El payload de la revocación de una cortesía.

    El MOTIVO es obligatorio: sin motivo no hay auditoría (`RN-P05`).
    """

    motivo: str = Field(
        ...,
        max_length=500,
        description="Motivo de la revocación. Obligatorio.",
    )


class AdminCortesiaRevocadaOut(BaseSchema):
    """Salida de la revocación de una cortesía.

    `ya_revocado` distingue la revocación EFECTIVA de la REPETICIÓN: la
    segunda no es un error, devuelve el mismo estado final (`FR-05` §2.3).
    """

    id: UUID = Field(..., description="Acta de la cortesía.")
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    pase_id: UUID = Field(..., description="Pase otorgado.")
    pase_nombre: str = Field(..., description="Nombre del pase.")
    persona_id: UUID = Field(..., description="Persona que recibió la cortesía.")
    persona_nombres: str = Field(..., description="Nombres de la persona.")
    persona_tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    persona_numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento de la persona.",
    )
    estado: str = Field(..., description="Estado de la cortesía.")
    motivo: str = Field(..., description="Motivo del otorgamiento.")
    motivo_revocacion: str = Field(
        default="",
        description="Motivo de la revocación.",
    )
    actor_usuario_id: UUID | None = Field(
        default=None,
        description="Cuenta que otorgó la cortesía.",
    )
    actor_nombres: str = Field(default="", description="Nombres de quien otorgó.")
    concedido_en: datetime = Field(..., description="Momento del otorgamiento.")
    revocado_en: datetime = Field(..., description="Momento de la revocación.")
    ya_revocado: bool = Field(
        ...,
        description=(
            "Si la cortesía YA estaba revocada: la operación es la REPETICIÓN "
            "idempotente, no un error."
        ),
    )


__all__ = [
    "AdminCortesiaListItemOut",
    "AdminCortesiaOut",
    "AdminCortesiaRevocadaOut",
    "AdminPaseListItemOut",
    "AsignarBeneficiarioIn",
    "CompraPaseCreadaOut",
    "ComprarPaseIn",
    "OtorgarCortesiaIn",
    "PaseBeneficiarioOut",
    "PaseBeneficiarioRevocadoOut",
    "PaseBeneficiariosOut",
    "PaseCompraDetalleOut",
    "PaseCatalogoOut",
    "PaseDetalleOut",
    "PaseEspecificoOut",
    "PaseGeneralOut",
    "PaseIdentidadOut",
    "PaseOut",
    "PrecioPaseOut",
    "RevocarCortesiaIn",
]
