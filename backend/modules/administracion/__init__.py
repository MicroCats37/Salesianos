"""
Administración operativa FEST — read-only aggregation module.

This module owns the `/administracion` HTTP namespace: the operational
dashboard of the active event (inscripciones, pagos, equipos, participantes,
acreditaciones, accesos, usuarios).

Design constraints (see `sdd/administracion-operativa-fest/admin-surface`):

- **No business tables.** The module declares NO models and NO migrations: it
  only reads the data owned by the business modules.
- **One-way dependency.** `administracion → business modules`. The admin
  module consumes the SELECTORS of the owning modules and never imports
  another module's `presentation/` layer
  (`contract/api-wrapper-presenter-contract.md` §1).
- **Read-only by construction.** No flows, no `transaction.atomic`, no write
  path. Any privileged mutation belongs to the flow of the owning business
  module.
- **One permission model.** `RequireAdmin` (admin = `is_staff OR is_superuser`)
  applied on the admin controllers: 401 anonymous, 403 authenticated non-admin.
"""
