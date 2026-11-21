"""Publicación de invalidaciones después del commit de un encuentro."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from .consumers import GRUPO_ENCUENTROS_PUBLICOS

SCHEMA_VERSION = 1


def publicar_encuentro_actualizado(encuentro_id: str) -> None:
    """Agenda el evento para que nunca se emita desde una transacción revertida."""

    def enviar() -> None:
        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            GRUPO_ENCUENTROS_PUBLICOS,
            {
                "type": "encuentro.actualizado",
                "payload": {
                    "type": "encuentro.actualizado",
                    "schema_version": SCHEMA_VERSION,
                    "encuentro_id": str(encuentro_id),
                    "occurred_at": timezone.now().isoformat(),
                },
            },
        )

    transaction.on_commit(enviar)
