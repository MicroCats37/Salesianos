"""`RegistroActivadoresCompra` — el índice de activadores por dominio de origen.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`
Contract: `contract/django-app-architecture-contract.md` §4.3

El coordinador de activación **conoce interfaces, no reglas de dominio**: no
sabe qué es un cupo, ni un pase, ni una salida de stock. Sólo sabe que hay
que activar el origen `INSCRIPCION`, `PASE` o `MARKETPLACE`, y pregunta a este
registro quién lo sabe hacer.

Cada dominio de origen registra SU activador (DOM-02 `inscripciones`,
DOM-03 `pases`, DOM-06 `marketplace`) sin tocar el código de `commerce`: por
eso el registro es un objeto **único del proceso** y no un binding de DI. Es
el mismo patrón que usa Django con sus propios registros de apps.

Mientras un dominio no registre su activador, la activación de ese origen
queda `PENDIENTE` y **reintentable**: el pago confirmado se conserva y el
operador ve que la entrega del derecho está en curso (RN-C08).
"""

import logging

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.ports import IActivadorDominioCompra

logger = logging.getLogger(__name__)


class RegistroActivadoresCompra:
    """Los activadores de dominio, indexados por origen de compra."""

    def __init__(self) -> None:
        self._activadores: dict[str, IActivadorDominioCompra] = {}

    def registrar(
        self,
        origen: str,
        activador: IActivadorDominioCompra,
    ) -> None:
        """Registra (o sustituye) el activador de un origen.

        Args:
            origen: uno de `OrigenCompra`.
            activador: la implementación del puerto del dominio.

        Raises:
            ValueError: si el origen no pertenece al vocabulario cerrado.
        """
        if origen not in OrigenCompra.values:
            raise ValueError("El origen de la activación no es válido.")
        self._activadores[origen] = activador

    def resolver(self, origen: str) -> IActivadorDominioCompra | None:
        """El activador de un origen, o `None` si todavía no lo hay."""
        return self._activadores.get(origen)

    def origenes_registrados(self) -> list[str]:
        """Los orígenes que ya tienen activador."""
        return sorted(self._activadores.keys())

    def limpiar(self) -> None:
        """Vacía el registro. Sólo lo usan las pruebas."""
        self._activadores.clear()


#: El registro único del proceso.
_REGISTRO = RegistroActivadoresCompra()


def obtener_registro() -> RegistroActivadoresCompra:
    """El registro de activadores del proceso.

    Es el mismo objeto para todos: un dominio que registra su activador lo
    hace UNA vez y el coordinador lo encuentra siempre.
    """
    return _REGISTRO


__all__ = [
    "RegistroActivadoresCompra",
    "obtener_registro",
]
