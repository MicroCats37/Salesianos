"""Result objects de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/django-app-architecture-contract.md` §4.6

Son DTOs INTERNOS (Pydantic puro). El presenter los traduce a los schemas
HTTP: un result NO es un schema de la API.

## Lo que estos results NO llevan

- **El token de gestión** de la compra de pases: es una credencial y sólo
  viaja en la respuesta que la emite.
- **Los identificadores internos del administrador**: el actor queda en el
  ACTA, no en la respuesta de negocio.
- **Ningún importe calculado por este módulo**: los importes son los que
  congeló el dueño de la compra.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ParticipanteAsistidoResultado(BaseModel):
    """La participación que la administración acaba de dar de alta.

    `estado` es el del DUEÑO (`EstadoParticipacion`): este módulo no publica
    un estado propio.
    """

    model_config = ConfigDict(frozen=True)

    participacion_id: str
    persona_id: str
    nombre: str
    documento: str
    equipo_id: str
    inscripcion_id: str
    rol: str
    estado: str


class CompraAsistidaResultado(BaseModel):
    """La compra asistida que la administración acaba de crear y liquidar.

    El `comprador` es el CLIENTE, nunca el administrador: es el hecho que
    hace auditable el comando.
    """

    model_config = ConfigDict(frozen=True)

    compra_id: str = Field(
        ...,
        description="La compra de `commerce` que financia la operación.",
    )
    recurso_id: str = Field(
        ...,
        description="El lote de pases o el pedido, según el tipo.",
    )
    orden_pago_id: str
    tipo: str = Field(..., description="PASE o PEDIDO.")
    concepto: str = Field(..., description="Concepto del bien comprado.")
    total: Decimal = Field(..., ge=0, description="Total congelado por el dueño.")
    moneda: str = Field(..., max_length=3, description="Moneda del total.")
    estado: str = Field(..., description="Estado del lote o del pedido.")
    estado_pago: str = Field(..., description="Estado del pago tras la aprobación.")
    comprador_persona_id: str
    comprador_nombre: str
    cantidad: int = Field(..., ge=1, description="Unidades compradas.")


__all__ = ["CompraAsistidaResultado", "ParticipanteAsistidoResultado"]
