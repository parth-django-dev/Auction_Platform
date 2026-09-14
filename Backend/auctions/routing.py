from django.urls import path
from .consumers import AuctionConsumer

websocket_urlpatterns = [
    path("ws/auction/<int:item_id>/", AuctionConsumer.as_asgi()),
]