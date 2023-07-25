#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/16 18:06
# @Author  : zhongzhilai
# @File    : enum.py
# @Description :

from enum import IntEnum


# 消息类型
class MessageEnum(IntEnum):
    GiftMessage = 0
    ChatMessage = 1
    EnterMessage = 2
    LikeMessage = 3
    InsertMessage = 9  # 插队消息


# 消息优先级
# 修改优先级需要配合gol.message_list中的顺序
class PriorityMessage(IntEnum):
    InsertPriority = 0  # 插队消息优先级
    GiftVip = 1
    GiftExpensive = 2
    DanmuVip = 3
    EnterHighLevel = 4
    GiftMiddle = 5
    DanmuExpensive = 6
    DanmuMiddle = 7
    GiftSmall = 8
    DanmuHighLevel = 9
    Danmu = 10
    Like = 11
