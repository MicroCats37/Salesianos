"""Los puertos de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

`IVerificadorDerecho` es la interfaz CONGELADA `VerificarDerecho` que los
módulos DUEÑOS implementan (`FR-05` §5).

`IEmisorCredencialService` es la interfaz de EMISIÓN: la declara el
CONSUMIDOR (`validaciones`) y la implementa el PRODUCTOR del derecho
(`salesianos_fest`). Es la inversión de dependencias que permite emitir una
credencial de un derecho ajeno SIN importar sus modelos
(`administracion-pases-alta-directa`, Apply C).
"""

from modules.validaciones.domain.ports.emisor_credencial import (
    IEmisorCredencialService,
    ReferenciaCredencial,
)
from modules.validaciones.domain.ports.verificador_derecho import (
    IVerificadorDerecho,
    TitularDerecho,
    VerificacionDerecho,
)

__all__ = [
    "IEmisorCredencialService",
    "IVerificadorDerecho",
    "ReferenciaCredencial",
    "TitularDerecho",
    "VerificacionDerecho",
]
