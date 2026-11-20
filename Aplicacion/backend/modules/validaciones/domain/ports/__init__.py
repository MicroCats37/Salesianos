"""Los puertos de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

`IVerificadorDerecho` es la interfaz CONGELADA `VerificarDerecho` que los
módulos DUEÑOS implementan (`FR-05` §5).
"""

from modules.validaciones.domain.ports.verificador_derecho import (
    IVerificadorDerecho,
    TitularDerecho,
    VerificacionDerecho,
)

__all__ = [
    "IVerificadorDerecho",
    "TitularDerecho",
    "VerificacionDerecho",
]
