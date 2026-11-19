"""Puertos (interfaces) del módulo `commerce`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Un puerto lo declara el módulo **consumidor** y lo implementa el módulo
**proveedor**. Aquí el consumidor es `commerce`: el coordinador pide a cada
dominio de origen que habilite SU derecho, y cada dominio responde con SU
propia implementación.

El coordinador **conoce interfaces, no reglas de dominio**: no sabe qué es un
cupo, ni un pase, ni una salida de stock. Sabe qué origen hay que activar y
qué clave de idempotencia hay que entregar.

| Puerto | Consume | Provee | Implementación |
|---|---|---|---|
| `IActivadorDominioCompra` | `commerce` (coordinador) | `inscripciones` / `pases` / `marketplace` | la implementa cada dominio (DOM-02, DOM-03, DOM-06) |

Los dobles de prueba de este puerto viven en
`modules/commerce/tests/fixtures/activacion_fakes.py`: son importables por
los tests de los dominios para no reescribir el contrato del puerto.
"""

from abc import ABC, abstractmethod

from modules.commerce.domain.schemas.compra_schemas import (
    ContextoActivacionCompra,
    ResultadoActivacionDominio,
)


class IActivadorDominioCompra(ABC):
    """La activación del derecho en el dominio de origen de la compra.

    Contrato para quien implemente el puerto (DOM-02 `inscripciones`,
    DOM-03 `pases`, DOM-06 `marketplace`):

    1. **La activación es idempotente por `contexto.clave`.** La clave es
       estable para una misma `(compra, origen)`: si el mismo derecho llega
       dos veces — un reintento, un webhook duplicado, un proceso que murió
       a mitad — el dominio debe aplicarlo **una sola vez**. El coordinador
       garantiza una sola *activación efectiva* por compra y origen; el
       dominio garantiza que su *aplicación* es idempotente.
    2. **El dominio conserva sus reglas.** El coordinador no decide cupos,
       passes, inventario ni elegibilidad: entrega el snapshot congelado y
       el dominio resuelve contra su propio catálogo.
    3. **El dominio no propaga secretos.** `ResultadoActivacionDominio.codigo`
       es un código de máquina (`[A-Z0-9_]`) y `detalle` sólo admite claves
       de una lista cerrada. El texto de una excepción **no** se devuelve.
    4. **El fallo del dominio no revierte el pago.** El coordinador registra
       la incidencia y expone un reintento seguro (RN-C08).
    """

    @abstractmethod
    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio:
        """Habilita el derecho que la compra pagó.

        Args:
            contexto: los hechos congelados de la compra y la clave estable
                de idempotencia de la activación.

        Returns:
            El resultado del dominio. `exito=False` significa "no se aplicó",
            no "se aplicó y falló": el derecho sigue sin concederse y la
            activación queda pendiente y reintentable.

        Raises:
            Exception: cualquier fallo del dominio. El coordinador lo
                captura, registra la incidencia y conserva el pago.
        """
        ...


__all__ = [
    "IActivadorDominioCompra",
]
