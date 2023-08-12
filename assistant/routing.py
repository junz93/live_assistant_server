from assistant.websocket import consumers
from django.urls import re_path

http_urlpatterns = [
    re_path(r'^stream/assistant/character/(?P<character_id>\d+)/generate_(?P<mode>chat|script)$', consumers.AiAnswerConsumer.as_asgi()),
    # re_path(r'^stream/assistant/character/(?P<character_id>\d+)/generate_script$', consumers.AiAnswerConsumer.as_asgi()),
]

websocket_urlpatterns = [
    re_path(r'^ws/assistant/live_prompt/(?P<platform>\w+)/(?P<room_id>\w+)$', consumers.LivePromptConsumer.as_asgi()),
]
