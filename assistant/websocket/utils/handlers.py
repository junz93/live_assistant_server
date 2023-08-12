import time
import datetime
import json
import logging
import os
import random
import threading

from assistant.models import Character
from assistant.services import gpt
# from assistant.services.gpt import get_answer, init_embedding
from channels.generic.websocket import WebsocketConsumer
from . import message as message_utils
from . import sqlite_conn
from .common_enum import MessageEnum, PriorityMessage
from .gol import Gol
from .message import get_user_level

# danmu_file = open('./logs/danmu.json', 'a', encoding='utf-8')
# gift_file = open('./logs/gift.json', 'a', encoding='utf-8')
# enter_file = open('./logs/enter.json', 'a', encoding='utf-8')
# like_file = open('./logs/like.json', 'a', encoding='utf-8')

message_path = "./conf/message_describe.json"
with open(message_path, "r", encoding="utf-8") as f:
    message_describe = json.load(f)

class MessageHandler:
    def __init__(self, danmu_consumer: WebsocketConsumer, gol: Gol, character: Character):
        self.danmu_consumer = danmu_consumer
        self.gol = gol
        self.character = character
        self.stop_requested = False

        t = threading.Thread(target=self.handle_message, daemon=True)
        t.start()

    def close(self):
        self.stop_requested = True

    def _deal_danmu(self, message_priority, chat_message):
        logging.info(f"\t处理弹幕中： {message_priority} -- {chat_message.user.nickName}: {chat_message.content}，线程id：{threading.get_ident()}，各优先级消息还剩余：{self.gol.get_all_list_num()}")

        # 过滤弹幕\昵称中的表情
        chat_message.content = message_utils.filer_biaoqing(chat_message.content)
        chat_message.content = message_utils.filter_emoji(chat_message.content)
        # 用户名称过滤
        chat_message.user.nickName = message_utils.filer_biaoqing(chat_message.user.nickName)
        chat_message.user.nickName = message_utils.filter_emoji(chat_message.user.nickName)
        chat_message.user.nickName = message_utils.filer_nickname(chat_message.user.nickName)

        answer = ''
        if chat_message.content:
            for segment in gpt.get_answer(chat_message.content, chat_message.user.id, chat_message.eventTime, character=self.character):
                if segment.startswith('抱歉'):
                    logging.warning('弹幕回答以“抱歉”开头，跳过')
                    return
                answer += segment
            # answer = ''.join(gpt.get_answer(chat_message.content, chat_message.user.id, chat_message.eventTime, character=self.character))
        # else:
        #     answer = ""

        if answer and not answer.startswith("生成Gpt回答出错，输入"):
            json_data = {
                'type': 'DANMU',
                'time': chat_message.eventTime,
                'userNickName': chat_message.user.nickName,
                'content': chat_message.content,
                'reply': answer,
            }
            self.danmu_consumer.send(text_data=json.dumps(json_data, ensure_ascii=False))
            logging.debug(f'Sent message to WS client: {json.dumps(json_data, ensure_ascii=False)}')

            user_priority = self.gol.get_user_priority(chat_message.common.roomId, chat_message.user)
            if user_priority <= 5 or user_priority == 7:
                sqlite_conn.db.insert_history_danmu(chat_message, answer)

        # if danmu_file is not None:
        #     msg = json.dumps({
        #         'danmu_time': datetime.datetime.fromtimestamp(chat_message.eventTime).isoformat(),
        #         'user_id': chat_message.user.id,
        #         'nickName': chat_message.user.nickName,
        #         'room_id': chat_message.common.roomId,
        #         'content': chat_message.content,
        #         'answer': answer,
        #     }, ensure_ascii=False)
        #     danmu_file.write(f'{msg}\n')
        #     danmu_file.flush()


    def _deal_gift(self, message_priority, gift_message):
        # start_time = time.time()
        try:
            logging.info(f"\t处理礼物中：{gift_message.common.describe}，线程id：{threading.get_ident()}，各优先级消息还剩余：{self.gol.get_all_list_num()}")
            # user_name = gift_message.user.nickName
            # gift_name = "{}个".format(gift_message.totalCount if gift_message.totalCount else "1") + gift_message.gift.describe.strip("送出")

            # if message_priority == PriorityMessage.GiftVip.value:
            #     gift_describe_template = random.choice(message_describe['vip_gift'])
            # elif message_priority == PriorityMessage.GiftExpensive.value:
            #     gift_describe_template = random.choice(message_describe['expensive_gift'])
            # elif message_priority == PriorityMessage.GiftMiddle.value:
            #     gift_describe_template = random.choice(message_describe['middle_gift'])
            # elif message_priority == PriorityMessage.GiftSmall.value:
            #     gift_describe_template = random.choice(message_describe['small_gift'])
            # else:
            #     logging.warning("当前礼物优先级不存在")
            #     return

            # gift_describe = gift_describe_template.format(user_name=user_name, gift_name=gift_name)

            gift_time = int(str(gift_message.sendTime)[:10])  # 异常：保留前10位
            json_data = {
                'type': 'GIFT',
                'time': gift_time,
                'userNickName': gift_message.user.nickName,
                'giftName': gift_message.gift.name,
                'count': gift_message.comboCount,
                # 'count': gift_message.repeatCount,
                # 'count': gift_message.totalCount if gift_message.totalCount else 1,
                'unitPrice': gift_message.gift.diamondCount * 10,  # Unit of price: cent
                'allTimeAmount': self.gol.get_history_user_gift(gift_message.common.roomId, gift_message.user.id) * 10,
                # 'reply': gift_describe,
            }
            self.danmu_consumer.send(text_data=json.dumps(json_data, ensure_ascii=False))
            logging.debug(f'Sent message to WS client: {json.dumps(json_data, ensure_ascii=False)}')

            # if gift_file is not None:
            #     msg = json.dumps({
            #         'gift_time': datetime.datetime.fromtimestamp(gift_time).isoformat(),
            #         'wav_time': datetime.datetime.fromtimestamp(start_time).isoformat(),
            #         'user_id': gift_message.user.id,
            #         'nickName': gift_message.user.nickName,
            #         'room_id': gift_message.common.roomId,
            #         'describe': gift_describe,
            #     }, ensure_ascii=False)
            #     gift_file.write(f'{msg}\n')
            #     gift_file.flush()
        except Exception as e:
            logging.exception(f"生成礼物回复出错")


    def _deal_enter(self, message_priority, member_message):
        try:
            room_id = member_message.common.roomId
            user_priority = self.gol.get_user_priority(room_id, member_message.user)
            # enter_message = random.choice(message_describe[f"enter_level{user_priority}"])

            logging.info(f"\t处理进入直播间观众消息中，用户名：{member_message.user.nickName}, 等级:{user_priority}，线程id：{threading.get_ident()}，各优先级消息还剩余：{self.gol.get_all_list_num()}")

            member_message.user.nickName = message_utils.filer_nickname(member_message.user.nickName)
            # enter_describe = enter_message.format(user_name=member_message.user.nickName)

            # TODO: 重要观众信息
            json_data = {
                'type': 'VIP_USER',
                # 'time': member_message.common.createTime,
                'time': int(time.time()),
                'userNickName': member_message.user.nickName,
                'userLevel': get_user_level(member_message.user),
                'allTimeAmount': self.gol.get_history_user_gift(room_id, member_message.user.id) * 10,
            }
            self.danmu_consumer.send(text_data=json.dumps(json_data, ensure_ascii=False))
            logging.debug(f'Sent message to WS client: {json.dumps(json_data, ensure_ascii=False)}')

            # generate_time = time.time()
            # get_wav(
            #     f"{enter_wav_dir}/{str(message_priority).zfill(2)}_{generate_time}/{str(message_priority).zfill(2)}_{generate_time}_000.wav",
            #     enter_describe)

            # if enter_file is not None:  # 多线程写入？
            #     msg = json.dumps({
            #         'generate_time': datetime.datetime.fromtimestamp(generate_time).isoformat(),
            #         'user_id': member_message.user.id,
            #         'nickName': member_message.user.nickName,
            #         'room_id': member_message.common.roomId,
            #         'describe': enter_describe,
            #     }, ensure_ascii=False)
            #     enter_file.write(f'{msg}\n')
            #     enter_file.flush()

        except Exception as e:
            logging.exception(f"生成进入直播间回复出错")


    # def _deal_like(self, message_priority, like_message):
    #     try:
    #         logging.info(f"\t处理点赞观众消息中，用户名：{like_message.user.nickName}, 线程id：{threading.get_ident()}，各优先级消息还剩余：{gol.get_all_list_num()}")
    #         user_name = message_utils.filter_emoji(like_message.user.nickName)
    #         user_name = message_utils.filer_biaoqing(user_name)
    #         user_name = message_utils.filer_nickname(user_name)
    #         like_describe = random.choice(message_describe["like_describe"]).format(user_name=user_name)

    #         generate_time = time.time()
    #         get_wav(
    #             f"{like_wav_dir}/{str(message_priority).zfill(2)}_{generate_time}/{str(message_priority).zfill(2)}_{generate_time}_000.wav",
    #             like_describe)

    #         if like_file is not None:  # 多线程写入？
    #             msg = json.dumps({
    #                 'generate_time': datetime.datetime.fromtimestamp(generate_time).isoformat(),
    #                 'user_id': like_message.user.id,
    #                 'nickName': like_message.user.nickName,
    #                 'room_id': like_message.common.roomId,
    #                 'describe': like_describe,
    #             }, ensure_ascii=False)
    #             like_file.write(f'{msg}\n')
    #             like_file.flush()

    #     except Exception as e:
    #         logging.exception(f"生成点赞回复出错，输入：{like_describe}\n异常：{e}")
    #     finally:
    #         ready_file = f"{like_wav_dir}/{str(message_priority).zfill(2)}_{generate_time}/{str(message_priority).zfill(2)}_{generate_time}_ready"
    #         try:
    #             if not os.path.exists(os.path.split(ready_file)[0]):
    #                 os.makedirs(os.path.split(ready_file)[0], exist_ok=True)
    #             open(ready_file, 'x').close()
    #             logging.info(f"生成点赞消息:{like_describe} 回复生成完成：{ready_file}")
    #         except Exception as e:
    #             traceback.print_exc()


    # def _deal_insert(self, message_priority, insert_message):
    #     try:
    #         if insert_message:
    #             logging.info(f"\t处理插队点赞观众消息中，用户名：{insert_message.user.nickName}, 线程id：{threading.get_ident()}，各优先级消息还剩余：{gol.get_all_list_num()}")
    #             user_name = message_utils.filter_emoji(insert_message.user.nickName)
    #             user_name = message_utils.filer_biaoqing(user_name)
    #             user_name = message_utils.filer_nickname(user_name)
    #             like_describe = random.choice(message_describe["like_describe"]).format(user_name=user_name)

    #             insert_time = time.time()
    #             get_wav(
    #                 f"{like_wav_dir}/{str(message_priority).zfill(2)}_{insert_time}/{str(message_priority).zfill(2)}_{insert_time}_000.wav",
    #                 like_describe)

    #         logging.info(f"\t生成插队求互动消息中")
    #         ask_time = time.time()
    #         ask_message = random.choice(message_describe["ask_like"] + message_describe["ask_gift"] + message_describe["ask_interaction"])
    #         get_wav(f"{insert_wav_dir}/{str(message_priority).zfill(2)}_{ask_time}/{str(message_priority).zfill(2)}_{ask_time}_000.wav", ask_message)

    #     except Exception as e:
    #         logging.exception(f"生成插队点赞回复出错，输入：{like_describe}\n异常：{e}")
    #     finally:
    #         if insert_message:
    #             ready_file = f"{insert_wav_dir}/{str(message_priority).zfill(2)}_{insert_time}/{str(message_priority).zfill(2)}_{insert_time}_ready"
    #             try:
    #                 if not os.path.exists(os.path.split(ready_file)[0]):
    #                     os.makedirs(os.path.split(ready_file)[0], exist_ok=True)
    #                 open(ready_file, 'x').close()
    #                 logging.info(f"插队消息:{like_describe} 生成完成：{ready_file}")
    #             except Exception as e:
    #                 traceback.print_exc()

    #         ask_file = f"{insert_wav_dir}/{str(message_priority).zfill(2)}_{ask_time}/{str(message_priority).zfill(2)}_{ask_time}_ready"
    #         try:
    #             if not os.path.exists(os.path.split(ask_file)[0]):
    #                 os.makedirs(os.path.split(ask_file)[0], exist_ok=True)
    #             open(ask_file, 'x').close()
    #             logging.info(f"求互动消息:{ask_message} 生成完成：{ask_file}")
    #         except Exception as e:
    #             traceback.print_exc()


    def handle_message(self):
        while True:
            try:
                if self.stop_requested:
                    break
                
                message_priority, message_type, message = self.gol.get_message()
                if message_type is None:
                    pass
                # elif message_type == MessageEnum.InsertMessage:
                #     self._deal_insert(message_priority, message)
                elif message_type == MessageEnum.GiftMessage:
                    self._deal_gift(message_priority, message)
                elif message_type == MessageEnum.ChatMessage:
                    self._deal_danmu(message_priority, message)
                elif message_type == MessageEnum.EnterMessage:
                    self._deal_enter(message_priority, message)
                # elif message_type == MessageEnum.LikeMessage:
                #     self._deal_like(message_priority, message)
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Failed to handle message", exc_info=True)


    def reload_embedding(self):
        while True:
            try:
                now = datetime.datetime.now()
                embedding_file = f"../data/embedding/embedding.pickle"
                realtime_file = f"../resource/实时信息.txt"
                # 不存在embedding文件或者实时信息文件的写入日期小于今天
                if not os.path.exists(embedding_file) or not os.path.exists(
                        realtime_file) or datetime.datetime.fromtimestamp(os.path.getmtime(realtime_file)).strftime(
                        "%Y-%m-%d") < now.strftime("%Y-%m-%d"):
                    gpt.init_embedding()
                time.sleep(5)
            except Exception as e:
                logging.exception(f"Failed to reload embedding.")
