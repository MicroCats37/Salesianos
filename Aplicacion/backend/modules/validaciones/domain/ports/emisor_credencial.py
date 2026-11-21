"""El puerto `IEmisorCredencialService`: la INTERFAZ entre módulos.

Change: `administracion-pases-alta-directa` · Apply C

La credencial (`Ticket`) REFERENCIA un derecho que ya existe en su módulo
DUEÑO. `validaciones` es el dueño de la credencial; el derecho es de
`salesianos_fest`. Para emitirla sin que `validaciones` importe los modelos
de `salesianos_fest`, este puerto invierte la dependencia:

- el CONSUMIDOR (`validaciones`) DECLARA el contrato que necesita;
- el PRODUCTOR (`salesianos_fest`) lo IMPLEMENTA.

**EL NAVEGADOR NO DECIDE EL TIPO.** El navegador sólo declara el IDENTIFICADOR
del derecho. El tipo (`PASE` / `ENTRADA_CORTESIA`) y la operación (`INGRESO`)
los DERIVA el módulo dueño del derecho, porque son hechos de SU dominio: una
cortesía y una compra no son la misma credencial.

**EL CÓDIGO NO VIENE DE AQUÍ.** La credencial se genera en el módulo que la
posee (`validaciones`), y es un SECRETO: se devuelve una sola vez, no se
publica en ningún listado y no se registra en la auditoría.

**SIN MOCKS.** `contract/TEST_ARCHITECTURE_CONTRACT.md` §6 prohíbe
`unittest.mock.patch`: las pruebas usan la base de datos real.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenciaCredencial:
    """La referencia al DERECHO sobre el que se emite la credencial.

    `derecho_id` es el identificador del derecho en su módulo dueño. `edicion_id`
    es el alcance de la credencial. `tipo_derecho` y `operacion` los DERIVA el
    dueño: son discriminantes cerrados, no texto libre.
    """

    derecho_id: str
    edicion_id: str
    tipo_derecho: str
    operacion: str


class IEmisorCredencialService(ABC):
    """El PRODUCTOR de la interfaz de emisión de credenciales.

    Un adaptador por módulo dueño. Hoy hay uno: `salesianos_fest`, que es el
    dueño de los derechos de ENTRADA (pase comprado y entrada de cortesía).

    El adaptador es SÍNCRÓNICO: se llama dentro de la transacción del flujo de
    `validaciones`.
    """

    @abstractmethod
    def resolver_referencia(self, derecho_id: str) -> ReferenciaCredencial:
        """Resuelve el derecho y deriva su tipo y su operación.

        Args:
            derecho_id: identificador del derecho en su módulo dueño.

        Returns:
            La referencia al derecho, con su tipo y su operación derivados.

        Raises:
            `PaseBeneficiarioNoEncontradoError`: el derecho no existe o no es
                de este dominio (404).
        """


__all__ = [
    "IEmisorCredencialService",
    "ReferenciaCredencial",
]
