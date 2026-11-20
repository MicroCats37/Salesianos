"""El puerto `VerificarDerecho`: la INTERFAZ congelada entre módulos.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §5 · `funcional/01` §5

La interfaz `VerificarDerecho` la PRODUCEN `pases`/`marketplace` y la CONSUME
`validaciones`. Su resultado es: puede usar/canjear, con razón y límite.

**QUIÉN POSEE LA REGLA.** El módulo dueño del derecho es el ÚNICO que puede
decir si un derecho se puede canjear y por qué. `validaciones` NO reimplanta
esas reglas (`FR-05` §1): las pide por este puerto.

**POR QUÉ EL PUERTO VIVE AQUÍ.** Es la inversión de dependencias: el
CONSUMIDOR declara el contrato que necesita y el PRODUCTOR lo implementa.

**SIN MOCKS.** `contract/TEST_ARCHITECTURE_CONTRACT.md` §6 prohíbe
`unittest.mock.patch`: las pruebas usan la base de datos real.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TitularDerecho:
    """La persona que sostiene el derecho.

    `persona_id` es el identificador de `usuarios.Persona`. `nombre` es el
    nombre que publica el módulo dueño: el navegador NUNCA lo compone con
    texto libre.
    """

    persona_id: str
    nombre: str


@dataclass(frozen=True)
class VerificacionDerecho:
    """Lo que el MÓDULO DUEÑO publica de un derecho.

    La forma reproduce la de `FR-05` §3.1: las tres cantidades están
    SIEMPRE presentes (expresan el consumo parcial sin prejuzgar `PD-03`),
    `puede_canjear` lo calcula el dueño y `motivo_codigo`/`motivo_mensaje`
    aparecen cuando NO se puede canjear. El mensaje es prosa pública SEGURA:
    nunca interpola identificadores.
    """

    tipo_derecho: str
    codigo: str
    titular: TitularDerecho
    edicion_id: str
    estado: str
    cantidad_total: int
    cantidad_consumida: int
    cantidad_disponible: int
    puede_canjear: bool
    motivo_codigo: str | None = None
    motivo_mensaje: str | None = None


class IVerificadorDerecho(ABC):
    """El PRODUCTOR de la interfaz `VerificarDerecho` (`FR-05` §5).

    Un adaptador por módulo dueño:

    - `resolver` es LECTURA: no muta, no consume, no escribe (`RN-P06`).
    - `consumir` es MUTACIÓN: revalida BAJO BLOQUEO y consume.

    `consumir` se llama SIEMPRE dentro de la transacción del flujo de
    `validaciones`: por eso es SINCRÓNICA y no abre su propia transacción.
    """

    #: El discriminante del módulo dueño que publica este adaptador.
    tipo_derecho: str = ""

    @abstractmethod
    def resolver(self, referencia_id: str) -> VerificacionDerecho:
        """Publica el estado del derecho SIN tocarlo.

        Raises:
            `TicketNoEncontradoError`: el derecho no existe.
        """

    @abstractmethod
    def consumir(
        self,
        referencia_id: str,
        cantidad: int,
        actor_usuario_id: str | None = None,
    ) -> VerificacionDerecho:
        """Revalida BAJO BLOQUEO y consume el derecho.

        Raises:
            `TicketNoEncontradoError`: el derecho no existe.
            `TicketYaConsumidoError`: no queda nada por consumir.
            `CantidadExcedidaError`: la cantidad pedida no se puede confirmar.
            `DerechoRevocadoError`: el derecho no está vigente.
        """


__all__ = [
    "IVerificadorDerecho",
    "TitularDerecho",
    "VerificacionDerecho",
]
