"""Re-export puro de los modelos del módulo `videos`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta `domain/models/`.
"""

from modules.videos.domain.models import Video

__all__ = ["Video"]
