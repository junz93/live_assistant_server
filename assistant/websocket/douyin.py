import gzip
import json
import logging
import re
import requests
import threading
import time
import urllib
import websocket

from assistant.models import Character
from assistant.services import content_censorship
from channels.generic.websocket import WebsocketConsumer
from google.protobuf import json_format
from protobuf_inspector.types import StandardParser
from .types.dy_pb2 import PushFrame
from .types.dy_pb2 import Response
from .types.dy_pb2 import MatchAgainstScoreMessage
from .types.dy_pb2 import LikeMessage
from .types.dy_pb2 import MemberMessage
from .types.dy_pb2 import GiftMessage
from .types.dy_pb2 import ChatMessage
from .types.dy_pb2 import SocialMessage
from .types.dy_pb2 import RoomUserSeqMessage
from .types.dy_pb2 import UpdateFanTicketMessage
from .types.dy_pb2 import CommonTextMessage
from .utils.gol import Gol
from .utils.handlers import MessageHandler

class DouyinLiveHandler:
    def __init__(self, ws_consumer: WebsocketConsumer, character: Character):
        self.gol = Gol('douyin')
        self.message_handler = MessageHandler(ws_consumer, self.gol, character)
        # gol._init("douyin")

        # Event for stop signal
        self.stop_event = threading.Event()
        # All ws connections with douyin danmu server
        self.ws_connections = []
        # The next ws connection to restart
        self.next_ws_connection_index = 0
        self.processed_message_ids = set()
        self.processed_message_lock = threading.Lock()

    def close(self):
        self.stop_event.set()
        self.message_handler.close()

    def _on_message(self, ws: websocket.WebSocketApp, message: bytes):
        wssPackage = PushFrame()
        wssPackage.ParseFromString(message)
        logId = wssPackage.logId
        decompressed = gzip.decompress(wssPackage.payload)
        payloadPackage = Response()
        payloadPackage.ParseFromString(decompressed)
        # 发送ack包
        if payloadPackage.needAck:
            self._sendAck(ws, logId, payloadPackage.internalExt)
        for msg in payloadPackage.messagesList:
            if msg.method == 'WebcastLikeMessage':
                self._unPackWebcastLikeMessage(msg.payload)
            elif msg.method == 'WebcastMemberMessage':
                self._unPackWebcastMemberMessage(msg.payload)
            elif msg.method == 'WebcastGiftMessage':
                self._unPackWebcastGiftMessage(msg.payload)
            elif msg.method == 'WebcastChatMessage':
                self._unPackWebcastChatMessage(msg.payload)
            # elif msg.method == 'WebcastMatchAgainstScoreMessage':
            #     self._unPackMatchAgainstScoreMessage(msg.payload)
            # elif msg.method == 'WebcastSocialMessage':
            #     self._unPackWebcastSocialMessage(msg.payload)
            # elif msg.method == 'WebcastRoomUserSeqMessage':
            #     self._unPackWebcastRoomUserSeqMessage(msg.payload)
            # elif msg.method == 'WebcastUpdateFanTicketMessage':
            #     self._unPackWebcastUpdateFanTicketMessage(msg.payload)
            # elif msg.method == 'WebcastCommonTextMessage':
            #     self._unPackWebcastCommonTextMessage(msg.payload)
            # else:
            #     logging.info('[onMessage] [⌛️方法' + msg.method + '等待解析～]')

    # 弹幕
    def _unPackWebcastChatMessage(self, data):
        # get_time = datetime.datetime.fromtimestamp(round(time.time())).isoformat(),
        chatMessage = ChatMessage()
        chatMessage.ParseFromString(data)

        with self.processed_message_lock:
            if chatMessage.common.msgId in self.processed_message_ids:
                logging.info(f'Skipped duplicate message {chatMessage.common.msgId}')
                return data
            self.processed_message_ids.add(chatMessage.common.msgId)

        # Aliyun 文本审核
        if not content_censorship.check_text(chatMessage.content):
            return data

        self.gol.add_danmu_list(chatMessage)
        # logging.info(f"[📧直播间弹幕消息] ｜ {chatMessage.user.nickName}: {chatMessage.content}，各优先级消息还剩余：{self.gol.get_all_list_num()}")

        # data_dict = json_format.MessageToDict(chatMessage, preserving_proto_field_name=True)
        return data

    # 礼物
    def _unPackWebcastGiftMessage(self, data):
        giftMessage = GiftMessage()
        giftMessage.ParseFromString(data)

        with self.processed_message_lock:
            if giftMessage.common.msgId in self.processed_message_ids:
                logging.info(f'Skipped duplicate message {giftMessage.common.msgId}')
                return data
            self.processed_message_ids.add(giftMessage.common.msgId)

        # data_dict = json_format.MessageToDict(giftMessage, preserving_proto_field_name=True)

        # 有combo参数 并且 不是最后一次跳过
        if giftMessage.gift.combo and not giftMessage.repeatEnd:
            return data

        gift_amount = giftMessage.gift.diamondCount * giftMessage.comboCount
        # logging.info(
            # f'[🎁直播间礼物消息] ｜ {giftMessage.common.describe}  金额：{giftMessage.gift.diamondCount} x {giftMessage.comboCount} = {gift_amount}，各优先级消息还剩余：{self.gol.get_all_list_num()}')
        self.gol.add_gift_list(giftMessage)

        return data

    # 进入直播间
    def _unPackWebcastMemberMessage(self, data):
        memberMessage = MemberMessage()
        memberMessage.ParseFromString(data)
        with self.processed_message_lock:
            if memberMessage.common.msgId in self.processed_message_ids:
                logging.info(f'Skipped duplicate message {memberMessage.common.msgId}')
                return data
            self.processed_message_ids.add(memberMessage.common.msgId)

        self.gol.add_enter_list(memberMessage)

        # data_dict = json_format.MessageToDict(memberMessage, preserving_proto_field_name=True)
        # logging.info('[unPackWebcastMemberMessage] [🚹🚺直播间进入消息] ｜ \n' + json.dumps(data_dict, ensure_ascii=False))
        return data

    # 点赞
    def _unPackWebcastLikeMessage(self, data):
        likeMessage = LikeMessage()
        likeMessage.ParseFromString(data)
        with self.processed_message_lock:
            if likeMessage.common.msgId in self.processed_message_ids:
                logging.info(f'Skipped duplicate message {likeMessage.common.msgId}')
                return data
            self.processed_message_ids.add(likeMessage.common.msgId)

        self.gol.add_like_list(likeMessage)
        # logging.info(f'[👍直播间点赞消息]｜ 用户名称：{likeMessage.user.nickName}  用户id：{likeMessage.user.id} ')

        # data_dict = json_format.MessageToDict(likeMessage, preserving_proto_field_name=True)
        # logging.info('[unPackWebcastLikeMessage] [👍直播间点赞消息] ｜ ' + json.dumps(data_dict, ensure_ascii=False))
        return data

    # 发送Ack请求
    def _sendAck(self, ws: websocket.WebSocketApp, logId, internalExt):
        obj = PushFrame()
        obj.payloadType = 'ack'
        obj.logId = logId
        obj.payloadType = internalExt
        data = obj.SerializeToString()
        ws.send(data, websocket.ABNF.OPCODE_BINARY)
        # logging.info('[sendAck] [🌟发送Ack]')

    def _on_error(self, ws: websocket.WebSocketApp, error):
        logging.error(f'[onError] [webSocket Error事件]. Error: {type(error)} - {str(error)}')

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code, close_status_msg):
        logging.info('[onClose] [webSocket Close事件]')

    def _on_open(self, ws: websocket.WebSocketApp):
        ping_thread = threading.Thread(target=self._ping, args=[ws])
        ping_thread.start()
        logging.info('[onOpen] [webSocket Open事件]')

    # 发送ping心跳包
    def _ping(self, ws: websocket.WebSocketApp):
        n = 0
        try:
            while True:
                if self.stop_event.is_set():
                    ws.close()
                    break
                if n == 10:
                    n = 0
                    obj = PushFrame()
                    obj.payloadType = 'hb'
                    data = obj.SerializeToString()
                    ws.send(data, websocket.ABNF.OPCODE_BINARY)
                    logging.info('[💗发送ping心跳]')
                else:
                    n += 1
                time.sleep(1)
        except websocket.WebSocketConnectionClosedException as e:
            logging.info(f'Terminating the ping thread. Exception: {e}')
        except Exception as e:
            raise e

    def _start_ws_server(self, internal_room_id, user_unique_id, ttwid):
        websocket.enableTrace(False)
        websocket_url = 'wss://webcast3-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:'+internal_room_id+'|wss_push_did:'+user_unique_id+'|dim_log_id:202302171547011A160A7BAA76660E13ED|fetch_time:1676620021641|seq:1|wss_info:0-1676620021641-0-0|wrds_kvs:WebcastRoomStatsMessage-1676620020691146024_WebcastRoomRankMessage-1676619972726895075_AudienceGiftSyncData-1676619980834317696_HighlightContainerSyncData-2&cursor=t-1676620021641_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id='+user_unique_id+'&device_platform=web&cookie_enabled=true&screen_width=1440&screen_height=900&browser_language=zh&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0%20(Macintosh;%20Intel%20Mac%20OS%20X%2010_15_7)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/110.0.0.0%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id='+internal_room_id+'&heartbeatDuration=0&signature=00000000'
        # websocket_url = 'wss://webcast3-ws-web-lq.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:'+internal_room_id+'|wss_push_did:'+user_unique_id+'|dim_log_id:202302171547011A160A7BAA76660E13ED|fetch_time:1676620021641|seq:1|wss_info:0-1676620021641-0-0|wrds_kvs:WebcastRoomStatsMessage-1676620020691146024_WebcastRoomRankMessage-1676619972726895075_AudienceGiftSyncData-1676619980834317696_HighlightContainerSyncData-2&cursor=t-1676620021641_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id='+user_unique_id+'&device_platform=web&cookie_enabled=true&screen_width=1440&screen_height=900&browser_language=zh&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0%20(Macintosh;%20Intel%20Mac%20OS%20X%2010_15_7)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/110.0.0.0%20Safari/537.36&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id='+internal_room_id+'&heartbeatDuration=0&signature=Rk7kMWh+wzXKrKP2'
        h = {
            'cookie': "ttwid=" + ttwid,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        }
        # 创建一个长连接
        ws = websocket.WebSocketApp(
            websocket_url, 
            header=h,
            on_message=self._on_message, 
            on_error=self._on_error, 
            on_close=self._on_close,
            on_open=self._on_open,
        )

        self.ws_connections.append(ws)
        while True:
            logging.info('Starting WebSocket infinite event loop...')
            ws.run_forever()
            if self.stop_event.is_set():
                logging.info('Terminated the WS event loop with danmu server as requested')
                break
            logging.warning('Encountered an error while in WS infinite loop. Reconnecting...')
            ws.close()
            time.sleep(10)

    def start_danmu_handler(self, room_id, num_threads=1):
        url = f'https://live.douyin.com/{room_id}'
        h = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'cookie': '__ac_nonce=0638733a400869171be51',
        }
        res = requests.get(url=url, headers=h)
        data = res.cookies.get_dict()
        ttwid = data['ttwid']
        res = res.text
        res = re.search(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', res)
        res = res.group(1)
        res = urllib.parse.unquote(res, encoding='utf-8', errors='replace')
        res = json.loads(res)
        room_store = res['app']['initialState']['roomStore']
        internal_room_id = room_store['roomInfo']['roomId']
        # room_title = room_store['roomInfo']['room']['title']
        user_unique_id = res['app']['odin']['user_unique_id']
        logging.info(f'Retrieved information for the live room. Room ID: {internal_room_id}, user unique ID: {user_unique_id}')
        
        for i in range(num_threads):
            thread = threading.Thread(target=self._start_ws_server, args=[internal_room_id, user_unique_id, ttwid], daemon=True)
            thread.start()

        # Runs forever
        # _schedule_restart_websocket(num_threads)

    def _schedule_restart_websocket(self, num_ws_connections=1):
        global next_ws_connection_index

        while len(self.ws_connections) < num_ws_connections:
            time.sleep(0.1)
        
        # Restart each ws connection every 2 minutes
        restart_interval = 120 / num_ws_connections
        while True:
            time.sleep(restart_interval)
            self.ws_connections[next_ws_connection_index].close()
            logging.info(f'Closed the websocket connection {next_ws_connection_index}')
            next_ws_connection_index = (next_ws_connection_index + 1) % len(self.ws_connections)
