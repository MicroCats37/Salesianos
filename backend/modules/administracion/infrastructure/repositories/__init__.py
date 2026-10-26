"""
Repositories — EMPTY on purpose.

`contract/django-app-architecture-contract.md` §9: no repository layer is
created just to wrap the Django ORM. The ORM is already the persistence
abstraction, and this module only reads it through the selectors of the
business modules.
"""
