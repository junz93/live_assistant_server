import json
import logging
import threading
import time

from assistant.models import Character
from channels.generic.websocket import WebsocketConsumer
from urllib.parse import parse_qs
from .douyin import DouyinLiveHandler
from .utils.handlers import MessageHandler

class DanmuInteractionConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
        # super().__init__(*args, **kwargs)

    def connect(self):
        self.accept()
        logging.info('Websocket connection opened with client (browser)')

        path_params = self.scope['url_route']['kwargs']
        query_params = parse_qs(self.scope['query_string'].decode(encoding='utf-8'))

        print(query_params)
        
        if 'platform' not in path_params \
            or 'room_id' not in path_params \
            or 'character_id' not in query_params:
            logging.warning('Bad request. Closing WS connection...')
            self.close()
            return

        self.platform = path_params['platform']
        self.room_id = path_params['room_id']
        character_id = query_params['character_id'][0]

        try:
            self.live_handler = None
            character = Character.objects.get(id=int(character_id))
            self.live_handler = DouyinLiveHandler(self, character)
            self.live_handler.start_danmu_handler(self.room_id)
        except Exception as e:
            logging.error('Failed to start live handler', exc_info=True)
            self.close()
            return

        # self.message_handler = MessageHandler(self)
        # t = threading.Thread(target=self.message_handler.handle_message, daemon=True)
        # t.start()
        # douyin.start_danmu_handler(self.room_id)

        self.last_ping_time = time.time()
        threading.Thread(target=self._monitor_ping, daemon=True).start()
    
    def disconnect(self, code):
        logging.info(f'DanmuInteractionConsumer disconnected with code: {code}')
        # TODO: Cleanup
        if (self.live_handler):
            self.live_handler.close()

    def receive(self, text_data=None):
        if text_data:
            json_data = json.loads(text_data)
            if json_data['type'] == 'PING':
                logging.info('Received ping/heartbeat message from WS client')
                self.last_ping_time = time.time()

    def _monitor_ping(self):
        while True:
            if (time.time() - self.last_ping_time >= 40):
                # TODO: Cleanup
                # self.live_handler.close()
                # self.message_handler.stop_requested = True
                logging.info(f'No ping message in the last 30 seconds. Closing the WS connection...')
                self.close()
                break
            time.sleep(5)
