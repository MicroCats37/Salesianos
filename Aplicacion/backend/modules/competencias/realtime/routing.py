from django.urls import path

from .consumers import EncuentrosPublicosConsumer

websocket_urlpatterns = [
    path("ws/encuentros/", EncuentrosPublicosConsumer.as_asgi()),
]
