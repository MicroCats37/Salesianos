"""Módulo `pagos` — capa de pago agnóstica de dominio.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Este módulo es la **infraestructura compartida de pagos** (DEC-11). Es dueño de:

- `OrdenPago` — la obligación de pago de una compra.
- `TransaccionPago` — un **intento** contra el proveedor, con su historial.
- `RegistroIdempotencia` — la clave de idempotencia del borde HTTP (FR-04 §2.2).
- `EstadoOperativoPagoService` — el ÚNICO dueño del veredicto operativo
  (FR-01 §5.2). Ninguna otra superficie recalcula el veredicto cruzando hechos
  hermanos.

Lo que este módulo **NO** hace:

- No activa derechos de dominio (cupos, entradas, stock). Eso es FND-05
  (`RN-C08`: el cobro confirmado y la entrega del derecho son hechos separados).
- No conoce `Compra`: la relación con el agregado comercial viaja por un **port**
  (`domain/ports`), de modo que la dirección de dependencias queda
  `commerce -> pagos` y nunca se invierte.
"""

#: Versión congelada del contrato de presenters/schemas del módulo `pagos`.
#: El registro global vive en `core/contract_versions.py` (A0).
SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
