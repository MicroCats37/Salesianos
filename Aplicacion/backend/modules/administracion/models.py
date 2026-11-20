"""Re-export de los modelos del módulo `administracion`.

Regla de `contract/django-app-architecture-contract.md` §4.1: este archivo es
un re-export puro. NO contiene lógica.

`AccionAuditada` es el ACTA transversal de las acciones sensibles. El resto de
los datos que publica el panel pertenecen a su módulo DUEÑO.
"""

from .domain.models import AccionAuditada

__all__ = ["AccionAuditada"]
