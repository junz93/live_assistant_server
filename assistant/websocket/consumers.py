import json
import logging
import threading
import time

from channels.generic.websocket import WebsocketConsumer
from . import douyin
from .utils.handlers import MessageHandler

class DanmuInteractionConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
        # super().__init__(*args, **kwargs)

    def connect(self):
        self.accept()
        logging.info('Websocket connection opened with client (browser)')

        self.platform = self.scope['url_route']['kwargs']['platform']
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.message_handler = MessageHandler(self)
        t = threading.Thread(target=self.message_handler.handle_message, daemon=True)
        t.start()
        douyin.start_danmu_handler(self.room_id)

        self.last_ping_time = time.time()
        threading.Thread(target=self._monitor_ping, daemon=True).start()
    
    def disconnect(self, code):
        logging.info(f'DanmuInteractionConsumer disconnected with code: {code}')

    def receive(self, text_data=None):
        if text_data:
            json_data = json.loads(text_data)
            if json_data['message_type'] == 'ping':
                logging.info('Received ping/heartbeat message from WS client')
                self.last_ping_time = time.time()

    def _monitor_ping(self):
        while True:
            if (time.time() - self.last_ping_time >= 65):
                # TODO: Cleanup
                douyin.stop_event.set()
                self.message_handler.stop_requested = True
                logging.info(f'No ping message in the last 60 seconds. Closing the WS connection...')
                self.close()
                break
            time.sleep(5)
