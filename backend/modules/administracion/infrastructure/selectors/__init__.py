"""
Concrete selector implementations.

Empty on purpose: the administrative surface reads the data of the business
modules through THEIR selectors (`modules.eventos`, `modules.usuarios`,
`modules.salesianos_fest`), never through a second implementation of the same
query (`contract/django-app-architecture-contract.md` §4.12).
"""
