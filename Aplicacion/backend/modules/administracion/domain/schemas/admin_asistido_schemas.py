"""DTOs internos de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP.

## Los tres comandos que vive aquí

| Comando | Dueño del efecto | Qué resuelve este módulo |
|---|---|---|
| `AsignarParticipanteEquipoData` | `salesianos_fest` (`PoolFlujo`) | la identidad del equipo y su inscripción |
| `ComprarPaseParaClienteData` | `salesianos_fest` (`CompraPaseFlujo`) + `pagos` (`AprobarPagoManualFlujo`) | la identidad del cliente |
| `ComprarPedidoParaClienteData` | `marketplace` (`PedidoFlujo`) + `pagos` (`AprobarPagoManualFlujo`) | la identidad del cliente |

## La REGLA que gobierna los tres

**El COMPRADOR es el CLIENTE, nunca el administrador.** El administrador es el
ACTOR de la operación (queda en el acta) y NO es el dueño de la compra: la
identidad del cliente se resuelve por documento con la infraestructura de
identidades que ya existe (`IObtensionPersonaService.obtener_o_registrar`) y
se DECLARA al dueño del dominio.

**El PRECIO no viaja.** Ni el de un pase ni el de un producto: lo resuelve y
congela el dueño contra el catálogo vigente (`RN-C02`).

**El MOTIVO es obligatorio.** Los tres comandos son sensibles: sin motivo no
hay acta y sin acta no hay comando.
"""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ClienteAsistidoData(BaseModel):
    """La identidad CIVIL del cliente de una compra asistida.

    Es la misma identidad que declara un checkout invitado: tipo de
    documento, número, nombres, apellidos y correo de contacto. El correo NO
    habilita ningún derecho: es un dato de contacto.
    """

    tipo_documento: str = Field(..., max_length=3, description="Tipo de documento.")
    numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento.",
    )
    nombres: str = Field(..., max_length=255, description="Nombres del cliente.")
    apellidos: str = Field(default="", max_length=255, description="Apellidos del cliente.")
    contacto_email: str = Field(
        default="",
        max_length=255,
        description="Correo de contacto. No habilita ningún derecho.",
    )


class EvidenciaPagoAsistidoData(BaseModel):
    """La EVIDENCIA del pago externo que el administrador registra.

    Es la misma evidencia que exige la aprobación manual del pago
    (`AprobarPagoManualIn`): un canal, una referencia y un motivo. La
    liquidación la aplica el DUEÑO (`AprobarPagoManualFlujo`): este módulo
    no reimplementa ninguna transición de estado del pago.
    """

    canal: str = Field(..., max_length=32, description="Canal del pago externo.")
    referencia: str = Field(
        ...,
        max_length=100,
        description="Referencia, recibo u operación que prueba el pago.",
    )
    motivo: str = Field(..., max_length=1000, description="Motivo auditado.")


class AsignarParticipanteEquipoData(BaseModel):
    """La intención de agregar una persona EXISTENTE a la plantilla de un equipo.

    La persona se identifica por DOCUMENTO EXACTO (tipo + número): es la
    única forma que la interfaz de administración conoce de un tercero. No
    viaja ningún identificador interno: el documento no es una credencial
    (`RN-U04`).

    Las REGLAS (capacidad, duplicado, disciplina, compatibilidad de género) NO
    viajan y NO se comprueban aquí: las aplica el dueño
    (`PoolFlujo.agregar_participante`).
    """

    equipo_id: UUID = Field(..., description="Equipo de destino.")
    tipo_documento: str = Field(..., max_length=3, description="Tipo de documento.")
    numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento de la persona.",
    )
    rol: str = Field(default="JUGADOR", max_length=16, description="Rol en el equipo.")
    motivo: str = Field(..., max_length=1000, description="Motivo auditado.")


class ComprarPaseParaClienteData(BaseModel):
    """La intención de comprar un lote de pases PARA un cliente."""

    pase_id: UUID = Field(..., description="Pase del catálogo que se compra.")
    cantidad: int = Field(..., ge=1, description="Número de pases que se compran.")
    cliente: ClienteAsistidoData = Field(..., description="Identidad del cliente.")
    evidencia: EvidenciaPagoAsistidoData = Field(
        ...,
        description="Evidencia del pago externo que se registra.",
    )


class ItemPedidoAsistidoData(BaseModel):
    """Un artículo del pedido de tienda que se compra PARA un cliente."""

    tipo: str = Field(default="PRODUCTO", max_length=16, description="Tipo de concepto.")
    producto_id: UUID = Field(..., description="Identificador del producto.")
    cantidad: int = Field(..., ge=1, description="Cantidad pedida.")


class ComprarPedidoParaClienteData(BaseModel):
    """La intención de comprar un pedido de tienda PARA un cliente."""

    items: list[ItemPedidoAsistidoData] = Field(
        ...,
        min_length=1,
        description="Artículos del pedido.",
    )
    cliente: ClienteAsistidoData = Field(..., description="Identidad del cliente.")
    evidencia: EvidenciaPagoAsistidoData = Field(
        ...,
        description="Evidencia del pago externo que se registra.",
    )

    @model_validator(mode="after")
    def _pedido_con_articulos(self) -> "ComprarPedidoParaClienteData":
        """Un pedido tiene al menos un artículo."""
        if not self.items:
            raise ValueError("El pedido necesita al menos un artículo.")
        return self


__all__ = [
    "AsignarParticipanteEquipoData",
    "ClienteAsistidoData",
    "ComprarPaseParaClienteData",
    "ComprarPedidoParaClienteData",
    "EvidenciaPagoAsistidoData",
    "ItemPedidoAsistidoData",
]
