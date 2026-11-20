"""El REGISTRO de adaptadores del puerto `VerificarDerecho`.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §5

Un adaptador por MÓDULO DUEÑO. El registro los reúne y reparte por el
discriminante del derecho (`tipo_derecho`).

Los adaptadores viven en su propio módulo dueño (`salesianos_fest`,
`marketplace`): este archivo sólo los conecta. El `import` es perezoso para
que un módulo que no use una operación no cargue el otro.
"""

from modules.validaciones.domain.constants import TipoDerechoChoices
from modules.validaciones.domain.exceptions import VerificadorNoDisponibleError
from modules.validaciones.domain.ports.verificador_derecho import IVerificadorDerecho


class RegistroVerificadoresDerecho:
    """El directorio de adaptadores: un dueño por tipo de derecho."""

    def __init__(self, adaptadores: dict[str, IVerificadorDerecho] | None = None):
        self._adaptadores = dict(adaptadores or _adaptadores_por_defecto())

    def verificador_de(self, tipo_derecho: str) -> IVerificadorDerecho:
        """El adaptador del dueño de ese tipo de derecho."""
        verificador = self._adaptadores.get(tipo_derecho)
        if verificador is None:
            raise VerificadorNoDisponibleError(tipo_derecho)
        return verificador

    @property
    def tipos(self) -> tuple[str, ...]:
        """Los tipos de derecho que este registro puede verificar."""
        return tuple(sorted(self._adaptadores))


def _adaptadores_por_defecto() -> dict[str, IVerificadorDerecho]:
    """Los adaptadores reales de los módulos dueño."""
    from modules.marketplace.domain.services.core.verificador_derecho_pedido import (
        PedidoVerificadorDerecho,
    )
    from modules.salesianos_fest.domain.services.core.verificador_derecho_pase import (
        PaseVerificadorDerecho,
    )

    return {
        TipoDerechoChoices.PASE: PaseVerificadorDerecho(),
        TipoDerechoChoices.ENTRADA_CORTESIA: PaseVerificadorDerecho(),
        TipoDerechoChoices.PRODUCTO: PedidoVerificadorDerecho(),
    }


__all__ = [
    "RegistroVerificadoresDerecho",
]
