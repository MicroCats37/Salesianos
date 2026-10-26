"""
Models — the administracion module declares NO business tables.

`contract/django-app-architecture-contract.md` §4.1: the root `models.py` is a
pure re-export and never holds logic. Here the re-export is EMPTY on purpose:
the administrative surface is a read-only AGGREGATION over the tables owned by
the business modules (`modules.salesianos_fest`, `modules.usuarios`,
`modules.eventos`, `modules.commerce`, `modules.pagos`).

Consequences, all intentional:
- no model class, therefore no migration for this app;
- the admin module can never mutate business state by accident;
- the business modules keep the authority over their own data.

A new table would only be justified by a domain rule that the current modules
cannot express — never to store a dashboard snapshot.
"""

__all__ = []
