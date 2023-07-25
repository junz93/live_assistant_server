from assistant.websocket import consumers
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'^ws/assistant/danmu/(?P<platform>\w+)/(?P<room_id>\w+)/$', consumers.DanmuInteractionConsumer.as_asgi()),
]
