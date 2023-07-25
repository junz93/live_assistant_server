# -*- coding: utf-8 -*-
import logging
import time

from collections import defaultdict
from threading import Lock
from .common_enum import MessageEnum, PriorityMessage
from . import message
from . import sqlite_conn


class MessageCompare:
    def __init__(self, compare_num, message):
        self.compare_num = compare_num
        self.message = message

    def __lt__(self, other):
        try:
            return self.compare_num > other.compare_num
        except AttributeError:
            return NotImplemented


class Timer:
    def __init__(self, time=time.time()):
        self.time = time

    def tic(self):
        self.time = time.time()

    def toc(self):
        return time.time() - self.time


# 初始化
def _init(pf):
    global platform
    platform = pf
    global _insert_list  # 0
    _insert_list = []
    global _gift_vip_list  # 1
    _gift_vip_list = []
    global _gift_expensive_list  # 2
    _gift_expensive_list = []
    global _danmu_vip_list  # 3
    _danmu_vip_list = []
    global _enter_highlevel_list  # 4
    _enter_highlevel_list = []
    global _gift_middle_list  # 5
    _gift_middle_list = []
    global _danmu_expensive_list  # 6
    _danmu_expensive_list = []
    global _danmu_middle_list  # 7
    _danmu_middle_list = []
    global _gift_small_list  # 8
    _gift_small_list = []
    global _danmu_highlevel_list  # 9
    _danmu_highlevel_list = []
    global _danmu_list  # 10
    _danmu_list = []
    global _like_list  # 11
    _like_list = []

    global _insert_lock
    _insert_lock = Lock()
    global _gift_vip_lock
    _gift_vip_lock = Lock()
    global _gift_expensive_lock
    _gift_expensive_lock = Lock()
    global _danmu_vip_lock
    _danmu_vip_lock = Lock()
    global _enter_highlevel_lock
    _enter_highlevel_lock = Lock()
    global _gift_middle_lock
    _gift_middle_lock = Lock()
    global _danmu_expensive_lock
    _danmu_expensive_lock = Lock()
    global _danmu_middle_lock
    _danmu_middle_lock = Lock()
    global _gift_small_lock
    _gift_small_lock = Lock()
    global _danmu_highlevel_lock
    _danmu_highlevel_lock = Lock()
    global _danmu_lock
    _danmu_lock = Lock()
    global _like_lock
    _like_lock = Lock()

    global message_list
    message_list = [_insert_list, _gift_vip_list, _gift_expensive_list, _danmu_vip_list, _enter_highlevel_list, _gift_middle_list,
                    _danmu_expensive_list, _danmu_middle_list, _gift_small_list, _danmu_highlevel_list, _danmu_list,
                    _like_list]
    global message_lock
    message_lock = [_insert_lock, _gift_vip_lock, _gift_expensive_lock, _danmu_vip_lock, _enter_highlevel_lock, _gift_middle_lock,
                    _danmu_expensive_lock, _danmu_middle_lock, _gift_small_lock, _danmu_highlevel_lock, _danmu_lock,
                    _like_lock]

    global _insert_timer
    _insert_timer = Timer()

    # 记录用户所有送礼金额
    global _history_user_gift_dict
    _history_user_gift_dict = sqlite_conn.db.get_user_history_gift_amount()

    # 记录最近20条弹幕做去重
    global danmu_history_list
    danmu_history_list = []
    global danmu_history_lock
    danmu_history_lock = Lock()

    # 送礼用户优先回复弹幕数量
    global priority_danmu_num
    priority_danmu_num = defaultdict(int)
    global priority_danmu_num_lock
    priority_danmu_num_lock = Lock()

    # 感谢小礼物限制次数
    global _gift_small_limit_dict
    _gift_small_limit_dict = defaultdict(dict)
    _gift_small_limit_dict["global"] = {"time": time.time(), "num": 0}
    global _gift_small_limit_lock
    _gift_small_limit_lock = Lock()

    # 普通弹幕限制次数
    global _danmu_limit_dict
    _danmu_limit_dict = defaultdict(dict)
    _danmu_limit_dict["global"] = {"time": time.time(), "num": 0}
    global _danmu_limit_lock
    _danmu_limit_lock = Lock()

    # 点赞消息限制次数
    global _like_limit_dict
    _like_limit_dict = defaultdict(dict)
    _like_limit_dict["global"] = {"time": time.time(), "num": 0}
    global _like_limit_lock
    _like_limit_lock = Lock()


def get_user_priority(room_id, user_message):
    gift_amount = get_history_user_gift(room_id, user_message.id)
    if gift_amount >= 10000:
        return 1
    if gift_amount >= 5000:
        return 2
    if gift_amount >= 1000:
        return 3
    user_level = message.get_user_level(user_message)
    if platform == "douyin" and user_level >= 45 or platform == "bilibili" and user_level >= 21:
        return 4
    if gift_amount >= 520:
        return 5
    if platform == "douyin" and user_level >= 36 or platform == "bilibili" and user_level >= 16:
        return 6
    if gift_amount >= 1:
        return 7
    fans_level = message.get_fans_level(user_message)
    if fans_level > 0:
        return 8
    is_follow = user_message.FollowInfo.followStatus
    if is_follow:
        return 9

    return 10


def get_history_user_gift(room_id, user_id):
    return _history_user_gift_dict.get(f'{room_id}_{user_id}', 0)


def is_add_message(local_time, limit_dict, limit_lock, user_id, limit):
    g_mit, g_num, u_mit, u_num = limit
    if limit_dict["global"]["num"] >= g_num and local_time - limit_dict["global"]["time"] <= g_mit * 60:
        return False

    with limit_lock:
        if user_id not in limit_dict.keys():
            limit_dict[user_id] = {"time": time.time(), "num": 1}
        elif limit_dict[user_id]["num"] >= u_num and local_time - limit_dict[user_id][
            "time"] <= u_mit * 60: \
                return False
        # 更新user_id
        elif limit_dict[user_id]["time"] <= u_mit * 60:
            limit_dict[user_id]["num"] += 1
        elif limit_dict[user_id]["time"] > u_mit * 60:
            limit_dict[user_id] = {"time": time.time(), "num": 1}
        # 更新global
        elif local_time - limit_dict["global"]["time"] <= g_mit * 60:
            limit_dict["global"]["num"] += 1
        elif local_time - limit_dict["global"]["time"] > g_mit * 60:
            limit_dict["global"] = {"time": time.time(), "num": 1}

    return True


def add_gift_list(gift_message):
    user_id = gift_message.user.id
    room_id = gift_message.common.roomId
    gift_amount = gift_message.gift.diamondCount * gift_message.comboCount
    _history_user_gift_dict[f'{room_id}_{user_id}'] += gift_amount
    sqlite_conn.db.insert_history_gift(gift_message)

    if gift_amount >= 520:
        with _gift_vip_lock:
            _gift_vip_list.append(gift_message)
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuVip.value}_{user_id}"] += 5
    elif gift_amount >= 99:
        with _gift_expensive_lock:
            _gift_expensive_list.append(gift_message)
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuExpensive.value}_{user_id}"] += 3
    elif gift_amount >= 20:
        with _gift_middle_lock:
            _gift_middle_list.append(gift_message)
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuMiddle.value}_{user_id}"] += 2
    else:
        local_time = time.time()
        # 全局1分钟3次，单人2分钟1次
        is_add = is_add_message(local_time, _gift_small_limit_dict, _gift_small_limit_lock, user_id, (1, 3, 2, 1))
        if is_add:
            with _gift_small_lock:
                _gift_small_list.append(gift_message)


def add_danmu_list(chat_message):
    # 不包含中文
    if not message.is_contains_chinese(chat_message.content):
        logging.info(f"\t弹幕不含中文，跳过 -- {chat_message.user.nickName}: {chat_message.content}")
        return
    # 弹幕包含'@'
    if '@' in chat_message.content:
        logging.info(f"\t弹幕包含‘@’，跳过 -- {chat_message.user.nickName}: {chat_message.content}")
        return
    # 弹幕消息去重
    if any(message.str_repeat(danmu_history, chat_message.content, 0.6) for danmu_history in danmu_history_list):
        logging.info(f"\t弹幕重复，跳过 -- {chat_message.user.nickName}: {chat_message.content}")
        return
    with danmu_history_lock:
        if len(danmu_history_list) > 20:
            danmu_history_list.pop(0)
        danmu_history_list.append(chat_message.content)

    room_id = chat_message.common.roomId
    user_id = chat_message.user.id
    user_priority = get_user_priority(room_id, chat_message.user)
    if priority_danmu_num[f"{PriorityMessage.DanmuVip.value}_{user_id}"] > 0:
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuVip.value}_{user_id}"] -= 1
        with _danmu_vip_lock:
            _danmu_vip_list.append(chat_message)
    elif priority_danmu_num[f"{PriorityMessage.DanmuExpensive.value}_{user_id}"] > 0:
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuExpensive.value}_{user_id}"] -= 1
        with _danmu_expensive_lock:
            _danmu_expensive_list.append(chat_message)
    elif priority_danmu_num[f"{PriorityMessage.DanmuMiddle.value}_{user_id}"] > 0:
        with priority_danmu_num_lock:
            priority_danmu_num[f"{PriorityMessage.DanmuMiddle.value}_{user_id}"] -= 1
        with _danmu_middle_lock:
            _danmu_middle_list.append(chat_message)
    elif user_priority <= 2:
        if user_id not in priority_danmu_num.keys():
            with priority_danmu_num_lock:
                priority_danmu_num[f"{user_id}"] = 1
            with _danmu_highlevel_lock:
                _danmu_highlevel_list.append(chat_message)
    else:
        local_time = time.time()
        # 全局1分钟10次，单人2分钟5次
        is_add = is_add_message(local_time, _danmu_limit_dict, _danmu_limit_lock, user_id, (1, 10, 2, 5))
        if is_add:
            with _danmu_lock:
                _danmu_list.append(chat_message)


def add_enter_list(enter_message):
    room_id = enter_message.common.roomId
    user_priority = get_user_priority(room_id, enter_message.user)
    if user_priority <= 6:
        with _enter_highlevel_lock:
            _enter_highlevel_list.append(enter_message)


def add_like_list(like_message):
    user_id = like_message.user.id
    local_time = time.time()
    # 全局1分钟10次，单人2分钟1次
    is_add = is_add_message(local_time, _like_limit_dict, _like_limit_lock, user_id, (1, 10, 2, 1))
    if is_add:
        _like_list.append(like_message)


def add_insert_list(mtype, insert_message):
    if mtype == 'like':
        _insert_list.append(insert_message)


def get_list(_list, _lock):
    if len(_list) <= 0:
        return None
    else:
        with _lock:
            return _list.pop(0)


def get_all_list_num():
    res = []
    for _list in message_list:
        res.append(len(_list))
    return res


def get_message():
    for i, (_list, _lock) in enumerate(zip(message_list, message_lock)):
        # 插入消息单独处理
        if i == PriorityMessage.InsertPriority:
            if _insert_timer.toc() >= 3*60:
                with _like_lock:
                    message = _like_list.pop() if len(_like_list) > 0 else None
                    _like_list.clear()
                message_type = MessageEnum.InsertMessage

                _insert_timer.tic()
                return i, message_type, message

        # 其他消息
        else:
            message = get_list(_list, _lock)
            if message:
                if i in [PriorityMessage.GiftVip.value, PriorityMessage.GiftExpensive.value,
                         PriorityMessage.GiftMiddle.value, PriorityMessage.GiftSmall.value]:
                    message_type = MessageEnum.GiftMessage
                elif i in [PriorityMessage.DanmuVip.value, PriorityMessage.DanmuExpensive.value,
                           PriorityMessage.DanmuMiddle.value, PriorityMessage.DanmuHighLevel.value, PriorityMessage.Danmu.value]:
                    message_type = MessageEnum.ChatMessage
                elif i in [PriorityMessage.EnterHighLevel.value]:
                    message_type = MessageEnum.EnterMessage
                elif i in [PriorityMessage.Like.value]:
                    message_type = MessageEnum.LikeMessage
                else:
                    logging.warning("get_message：不存在的消息类型")
                    return None, None, None
                return i, message_type, message

    return None, None, None
