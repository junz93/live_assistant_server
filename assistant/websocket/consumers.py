import asyncio
import json
import logging
import threading
import time

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import WebsocketConsumer
from urllib.parse import parse_qs

from .douyin import DouyinLiveHandler
from assistant.models import Character
from assistant.services import gpt
from utils.userauth import is_usage_limit_reached


class LivePromptConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
        # super().__init__(*args, **kwargs)

    def connect(self):
        self.closed = False
        self.live_handler = None

        self.accept()
        logging.info('Websocket connection opened with client (browser)')

        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return
        if is_usage_limit_reached(user):
            self.close()
            return
        
        path_params = self.scope['url_route']['kwargs']
        query_params = parse_qs(self.scope['query_string'].decode(encoding='utf-8'))

        if 'platform' not in path_params \
            or 'room_id' not in path_params \
            or 'character_id' not in query_params:
            logging.warning('Bad request. Closing WS connection...')
            self.close()
            return

        self.platform = path_params['platform']
        self.room_id = path_params['room_id']
        character_id = int(query_params['character_id'][0])

        try:
            character = Character.objects.get(id=character_id, user_id=user.id)
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
        logging.info(f'LivePromptConsumer disconnected with code: {code}')
        # TODO: Cleanup
        self.closed = True
        if (self.live_handler):
            self.live_handler.close()

    def receive(self, text_data=None):
        if text_data:
            json_data = json.loads(text_data)
            if json_data['type'] == 'PING':
                logging.info('Received ping/heartbeat message from WS client')
                self.last_ping_time = time.time()

                # Send pong message to avoid connection being closed by nginx when idle for 60s
                # See http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout
                self.send(text_data=json.dumps({ 'type': 'PONG' }, ensure_ascii=False))

    # TODO: probably not needed especially when nginx is used (proxy_read_timeout)
    #       Also, the connection will be closed if the browser tab/window is closed
    def _monitor_ping(self):
        while True:
            if self.closed:
                break
            if (time.time() - self.last_ping_time >= 40):
                # TODO: Cleanup
                # self.live_handler.close()
                # self.message_handler.stop_requested = True
                logging.info(f'No ping message in the last 30 seconds. Closing the WS connection...')
                self.close()
                break
            time.sleep(5)


class AiAnswerConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        await self.send_headers(headers=[
            (b'Cache-Control', b'no-cache'),
            (b'Content-Type', b'text/event-stream; charset=utf-8'),
            # (b'Transfer-Encoding', b'chunked'),
        ])

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(403, 'Not logged in')
            return

        if await database_sync_to_async(is_usage_limit_reached)(user):
            await self.close(403, 'Max usage time was reached')
            return

        path_params = self.scope['url_route']['kwargs']
        query_params = parse_qs(self.scope['query_string'].decode(encoding='utf-8'))
        mode = path_params['mode'].upper()

        if 'character_id' not in path_params \
            or 'query' not in query_params \
            or (mode != gpt.AnswerMode.CHAT and mode != gpt.AnswerMode.SCRIPT):
            await self.close(400, 'Invalid input')
            return
        
        character_id = int(path_params['character_id'])
        query = query_params['query'][0]

        try:
            character = await self.get_character(character_id, user.id)
            # for segment in await sync_to_async(gpt.get_answer)(
            for segment in gpt.get_answer(
                query, 
                f'user_{user.id}' if mode == gpt.AnswerMode.CHAT else None, 
                int(time.time()), 
                with_censorship=False, 
                character=character, 
                mode=mode
            ):
                if segment.startswith('生成Gpt回答出错'):
                    await self.close(500, 'Failed to generate content')
                    return
                
                # logging.info('Received a segment')
                await self.send_message(segment)
                await asyncio.sleep(0.1)
            
            await self.close(200, 'Completed successfully')
        except Character.DoesNotExist:
            await self.close(404, f'Cannot find a character with ID {character_id}')
        except Exception as e:
            logging.exception('An error happened while generating content')
            await self.close(500, 'An error happened while generating content')

    @database_sync_to_async
    def get_character(self, character_id: int, user_id: int):
        return Character.objects.get(id=character_id, user_id=user_id)

    async def send_message(
        self, 
        data, 
        code: int = None, 
        message: str = None, 
        is_last = False
    ):
        json_data = { 'data': data }
        if code is not None:
            json_data['code'] = code
        if message is not None:
            json_data['message'] = message

        data = json.dumps(json_data, ensure_ascii=False)

        body = f'data: {data}\n\n'.encode('utf-8')
        await self.send_body(body, more_body=(not is_last))
    
    async def close(self, code: int, message: str):
        await self.send_message('', code, message, True)
