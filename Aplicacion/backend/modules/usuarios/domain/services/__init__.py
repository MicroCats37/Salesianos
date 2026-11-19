"""
Servicios de dominio del módulo `usuarios`.

Estructura (`contract/django-app-architecture-contract.md` §4.3–§4.5):

- `core/` — servicios SYNC, sin `transaction.atomic()` propia.
- `flujos/` — casos de uso ASYNC que abren la transacción.
- `orchestrators/` — fachadas async delgadas.
"""
