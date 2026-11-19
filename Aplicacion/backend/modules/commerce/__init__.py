"""Módulo `commerce` — el agregado comercial compartido.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Este módulo es dueño de `Compra`: el agregado comercial que los tres
dominios de venta comparten (DEC-11). Es dueño de:

- El snapshot de **lo comprado** y el **origen** de la compra.
- El **total congelado** por el servidor (`RN-C02`).
- La reutilización de una compra pendiente en vez de duplicarla (FR-04 I-4).

Lo que este módulo **NO** hace:

- No tiene superficie HTTP. Cada dominio crea su propia compra por su
  endpoint y su flujo (`RN-C01`, `DEC-10`): no existe un carrito conjunto.
- No conoce el detalle de lo comprado (paquetes, pases, productos): eso lo
  resuelven los dominios de origen, que entregan el snapshot ya congelado.
- No habilita derechos ni cobra: `pagos` es dueño del cobro y FND-05 lo es de
  la activación de derechos.
"""

#: Versión congelada del contrato de presenters/schemas del módulo
#: `commerce`. El registro global vive en `core/contract_versions.py` (A0).
SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
