from channels.generic.websocket import AsyncJsonWebsocketConsumer

GRUPO_ENCUENTROS_PUBLICOS = "competencias.encuentros.public"


class EncuentrosPublicosConsumer(AsyncJsonWebsocketConsumer):
    """Canal público, de solo lectura, para invalidar snapshots de encuentros."""

    async def connect(self):
        await self.channel_layer.group_add(GRUPO_ENCUENTROS_PUBLICOS, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GRUPO_ENCUENTROS_PUBLICOS, self.channel_name)

    async def encuentro_actualizado(self, event):
        await self.send_json(event["payload"])
