"""DTOs internos del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.6

Son DTOs de Pydantic **puros** (no schemas HTTP). Los schemas HTTP del
módulo `commerce` no existen: `commerce` no tiene superficie HTTP (el ledger
`FR-07` no le asigna ninguna ruta; cada dominio crea su propia compra por su
propio endpoint — `RN-C01`).

El módulo `pagos` es dueño del veredicto operativo; este módulo es dueño del
hecho comercial y del **snapshot de dinero**.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from modules.commerce.domain.constants import OrigenCompra


class LineaCompraSnapshot(BaseModel):
    """Una línea del snapshot inmutable de una compra.

    Es el **precio congelado**: aunque el precio vigente cambie después, la
    línea conserva el que se aplicó (`RN-M03`, FR-04 §1.1).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    concepto_tipo: str = Field(
        ...,
        max_length=40,
        description="Tipo de concepto comprado (paquete, pase, producto…).",
    )
    concepto_id: str = Field(
        ...,
        max_length=64,
        description="Identificador del concepto comprado.",
    )
    concepto_nombre: str = Field(
        ...,
        max_length=200,
        description="Nombre del concepto en el momento de la compra.",
    )
    cantidad: int = Field(..., gt=0, description="Cantidad comprada. Mayor que cero.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio unitario de catálogo en el momento de la compra.",
    )
    precio_aplicado: Decimal = Field(
        ...,
        ge=0,
        description=(
            "Precio unitario realmente aplicado (con oferta). Es el que "
            "multiplica la cantidad para el total."
        ),
    )

    @field_validator("precio_unitario", "precio_aplicado")
    @classmethod
    def _a_dos_decimales(cls, valor: Decimal) -> Decimal:
        """El dinero se congela a dos decimales, como la columna."""
        return valor.quantize(Decimal("0.01"))

    @property
    def subtotal(self) -> Decimal:
        """El subtotal de la línea: cantidad × precio aplicado."""
        return (self.precio_aplicado * self.cantidad).quantize(Decimal("0.01"))


class CompraCreateData(BaseModel):
    """Datos de la intención de compra.

    `total` es **opcional y sólo de contraste**: el total real lo calcula el
    servidor a partir de `lineas`. Si alguien declara un total, tiene que
    coincidir exactamente con el derivado; si no, la compra se rechaza
    (`RN-C02`).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    persona_id: UUID = Field(
        ...,
        description="UUID de la persona compradora. Obligatoria.",
    )
    origen: str = Field(
        ...,
        description="Dominio de origen de la compra.",
    )
    lineas: list[LineaCompraSnapshot] = Field(
        ...,
        min_length=1,
        description="Líneas del snapshot de la compra.",
    )
    referencia: str = Field(
        ...,
        max_length=200,
        description=(
            "Referencia de la intención de compra. Permite reutilizar la "
            "compra pendiente en vez de duplicarla."
        ),
    )
    moneda: str = Field(
        default="PEN",
        max_length=3,
        description="Código ISO-4217 del total.",
    )
    total: Decimal | None = Field(
        default=None,
        ge=0,
        description=(
            "Total declarado, sólo para contraste. El total que se congela es "
            "el que deriva de las líneas."
        ),
    )

    @field_validator("origen")
    @classmethod
    def _origen_conocido(cls, valor: str) -> str:
        """El origen pertenece al vocabulario cerrado."""
        if valor not in OrigenCompra.values:
            raise ValueError("El origen de la compra no es válido.")
        return valor

    @field_validator("moneda")
    @classmethod
    def _moneda_iso(cls, valor: str) -> str:
        """La moneda es un código ISO-4217 de tres letras."""
        texto = str(valor or "").strip().upper()
        if len(texto) != 3 or not texto.isalpha():
            raise ValueError("La moneda de la compra no es válida.")
        return texto


def calcular_total(lineas: list[LineaCompraSnapshot]) -> Decimal:
    """El total de una compra, derivado de sus líneas.

    Es la expresión de `RN-C02`: **el servidor congela el precio**. El total
    nunca se toma de lo que declara el cliente: se deriva de las líneas, que
    el módulo de origen resolvió contra el catálogo vigente.

    Args:
        lineas: las líneas del snapshot.

    Returns:
        El total con dos decimales.
    """
    total = sum((linea.subtotal for linea in lineas), Decimal("0.00"))
    return total.quantize(Decimal("0.01"))


class ContextoActivacionCompra(BaseModel):
    """Lo que el coordinador entrega al dominio para habilitar el derecho.

    Es la información **congelada** de la compra: el dominio no vuelve a
    consultar el catálogo ni a calcular el precio (RN-C02, RN-M03). El
    coordinador NO envía reglas del dominio: sólo hechos y la clave de
    idempotencia con la que el dominio puede deduplicar (FR-04 I-2).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    compra_id: UUID = Field(
        ...,
        description="UUID de la compra que financia el derecho.",
    )
    origen: str = Field(
        ...,
        description="Dominio de origen de la compra: el dispatch del coordinador.",
    )
    clave: str = Field(
        ...,
        max_length=128,
        description=(
            "Clave de idempotencia de la activación. Es ESTABLE entre "
            "reintentos: el dominio la usa para no aplicar el derecho dos veces."
        ),
    )
    persona_id: UUID = Field(
        ...,
        description="UUID de la persona compradora.",
    )
    referencia: str = Field(
        ...,
        max_length=200,
        description="Referencia de la intención de compra (la del dominio).",
    )
    total: Decimal = Field(
        ...,
        ge=0,
        description="Total congelado de la compra.",
    )
    moneda: str = Field(
        ...,
        max_length=3,
        description="Código ISO-4217 del total.",
    )
    lineas_snapshot: list[dict] = Field(
        default_factory=list,
        description="Snapshot inmutable de lo comprado (lo resuelve el dominio).",
    )

    @field_validator("origen")
    @classmethod
    def _origen_conocido(cls, valor: str) -> str:
        """El origen pertenece al vocabulario cerrado."""
        if valor not in OrigenCompra.values:
            raise ValueError("El origen de la activación no es válido.")
        return valor


class ResultadoActivacionDominio(BaseModel):
    """La respuesta del dominio a una activación.

    Deliberadamente **no** lleva texto libre: `codigo` es un código de
    máquina SEGURO y `detalle` sólo admite un conjunto CERRADO de claves con
    valores escalares. Así la incidencia que se persiste no puede filtrar
    identificadores, mensajes del proveedor ni secretos.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    exito: bool = Field(
        ...,
        description="Si el dominio aplicó el derecho.",
    )
    codigo: str = Field(
        default="",
        max_length=64,
        description=(
            "Código de máquina del resultado. Mayúsculas, dígitos y "
            "guiones bajos. Nunca texto libre."
        ),
    )
    detalle: dict = Field(
        default_factory=dict,
        description=(
            "Resumen informativo con claves de lista CERRADA. El "
            "coordinador descarta cualquier clave que no esté permitida."
        ),
    )


class ResultadoActivacionCompra(BaseModel):
    """El resultado de pedir la activación de los derechos de una compra.

    Lo consume el puerto de `pagos` y lo lee el operador. Es un hecho
    **público**: por eso lleva banderas y códigos, nunca identificadores
    internos ni mensajes de excepción.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    existe: bool = Field(
        ...,
        description="Si hay una compra que financia la orden.",
    )
    activada: bool = Field(
        default=False,
        description="Si el derecho quedó habilitado.",
    )
    ya_activada: bool = Field(
        default=False,
        description="Si el derecho ya estaba habilitado (repetición idempotente).",
    )
    en_curso: bool = Field(
        default=False,
        description="Si otro intento tiene la activación reservada.",
    )
    recuperable: bool = Field(
        default=False,
        description=(
            "Si la activación quedó pendiente por una incidencia que se puede "
            "reeintentar sin perder el pago confirmado (RN-C08)."
        ),
    )
    intentos: int = Field(
        default=0,
        description="Cuántos intentos de activación lleva la compra.",
    )
    codigo: str = Field(
        default="",
        max_length=64,
        description="Código de máquina del resultado de la activación.",
    )
    proxima_accion: str = Field(
        default="NINGUNA",
        max_length=40,
        description=(
            "La acción segura que sigue: `NINGUNA`, `REINTENTAR_ACTIVACION` "
            "o `ESPERAR_ACTIVACION`."
        ),
    )


__all__ = [
    "CompraCreateData",
    "ContextoActivacionCompra",
    "LineaCompraSnapshot",
    "ResultadoActivacionCompra",
    "ResultadoActivacionDominio",
    "calcular_total",
]
