"""`CompraOrchestrator` — fachada async del módulo `commerce`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Fachada MUY DELGADA: delega en el flujo y devuelve result objects, nunca
schemas HTTP. No contiene lógica de negocio.

`commerce` **no tiene superficie HTTP**: el ledger `FR-07` no le asigna
ninguna ruta. Cada dominio (inscripciones, pases, marketplace) crea su propia
compra por su propio endpoint y su propio flujo (`RN-C01`, `DEC-10`), y todas
terminan en este flujo compartido.
"""

from injector import inject

from modules.commerce.domain.schemas.compra_schemas import CompraCreateData
from modules.commerce.domain.selectors.compra_selector import CompraSelector
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo


class CompraOrchestrator:
    """Fachada async del módulo de compras."""

    @inject
    def __init__(self, flujo: CompraFlujo, selector: CompraSelector):
        self.flujo = flujo
        self.selector = selector

    async def crear_compra(self, data: CompraCreateData):
        """Crea la compra de una intención o reutiliza la pendiente.

        Returns:
            La tupla `(result, reutilizada)`.
        """
        compra, reutilizada = await self.flujo.crear_o_reutilizar_compra(data)
        return self.selector.como_result(compra, reutilizada=reutilizada), reutilizada


__all__ = ["CompraOrchestrator"]
