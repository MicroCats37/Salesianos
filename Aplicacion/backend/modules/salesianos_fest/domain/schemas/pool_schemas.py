"""DTOs internos del POOL y de la COMPRA de cupos extra.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP.

`FL-05` paso 2: "agrega persona existente **o** la resuelve por documento".
Por eso la persona se identifica de dos maneras excluyentes: por
identificador, o por documento. El DTO no valida esa exclusividad (es una
regla de negocio y vive en el servicio); sólo transporta los datos.
"""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ParticipanteAsignarData(BaseModel):
    """La intención de agregar (o reasignar) un participante al pool.

    `reemplaza_participacion_id` implementa el MOVIMIENTO de `FL-05` paso 4:
    la persona nueva toma el cupo de la retirada, en la MISMA transacción.
    """

    inscripcion_id: UUID | None = Field(
        default=None,
        description="Inscripción objetivo. La resuelve el orquestador.",
    )
    persona_id: UUID | None = Field(
        default=None,
        description="Persona ya existente del padrón.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Tipo de documento para resolver la persona.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento para resolver la persona.",
    )
    equipo_id: UUID = Field(..., description="Equipo de destino dentro de la inscripción.")
    rol: str = Field(
        default="JUGADOR",
        max_length=16,
        description="Rol de la persona en el equipo.",
    )
    reemplaza_participacion_id: UUID | None = Field(
        default=None,
        description=(
            "Participación que se retira para liberar su cupo. Es el MOVIMIENTO "
            "de cupo de `FL-05` paso 4."
        ),
    )

    @model_validator(mode="after")
    def _al_menos_una_forma_de_identificar(self) -> "ParticipanteAsignarData":
        """La persona se identifica por identificador O por documento."""
        por_identificador = self.persona_id is not None
        por_documento = bool(self.tipo_documento and self.numero_documento)
        if not por_identificador and not por_documento:
            raise ValueError(
                "La persona se identifica por identificador o por documento."
            )
        return self


class CompraCuposData(BaseModel):
    """La intención de comprar cupos extra para una inscripción.

    `cantidad` NO lleva un rango en el DTO: el límite lo declara y lo hace
    cumplir el DOMINIO, que responde con el código estable `CUPO_INVALIDO`
    (422) CONGELADO por el ledger para `RT-CM-01`. Si el DTO lo rechazara
    antes, el cliente vería `VALIDATION_ERROR` y el código congelado no
    llegaría nunca.
    """

    inscripcion_id: UUID | None = Field(
        default=None,
        description="Inscripción objetivo. La resuelve el orquestador.",
    )
    cantidad: int = Field(
        ...,
        description="Cantidad de cupos extra a comprar. El límite es del servidor.",
    )


__all__ = ["CompraCuposData", "ParticipanteAsignarData"]
