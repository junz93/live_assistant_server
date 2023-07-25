#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/21 15:03
# @Author  : zhongzhilai
# @File    : sqlite_conn.py
# @Description :

import logging
import sqlite3
import time
import traceback

from collections import defaultdict
from config_utils import db_config
from threading import Lock
from . import message as message_utils


class LiteDb(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def open_db(self, dbname="./db/test.db"):
        self.dbname = dbname
        self.conn = sqlite3.connect(self.dbname, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = Lock()

    def close_db(self):
        self.cursor.close()
        self.conn.close()

    def get_user_history_gift_amount(self):
        with self.lock:
            sql = "SELECT room_id, user_id, sum(amount_sum) from gift_history where valid = 1 group by room_id, user_id"
            self.cursor.execute(sql)
            res = defaultdict(int)
            for row in self.cursor.fetchall():
                res[f"{row[0]}_{row[1]}"] = int(row[2])
            return res

    def insert_history_gift(self, gift_message):
        try:
            with self.lock:
                room_id = gift_message.common.roomId
                user_id = gift_message.user.id
                user_level = message_utils.get_user_level(gift_message.user)
                gift_id = gift_message.gift.id
                gift_name = gift_message.gift.name
                gift_amount = gift_message.gift.diamondCount
                gift_num = gift_message.comboCount
                amount_sum = gift_message.gift.diamondCount * gift_message.comboCount
                ins_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(gift_message.sendTime)[:10])))

                sql = f"INSERT INTO gift_history (room_id,user_id,user_level,gift_id,gift_name, gift_amount,gift_num,amount_sum,time)" \
                      f"VALUES ('{room_id}','{user_id}',{user_level},{gift_id},'{gift_name}', {gift_amount},{gift_num},{amount_sum},'{ins_time}')"
                self.cursor.execute(sql)
                self.conn.commit()
        except Exception as e:
            logging.info("！！！插入礼物数据失败！！！")
            traceback.print_exc()
            logging.info(gift_message)

    def insert_history_danmu(self, chat_message, answer):
        try:
            with self.lock:
                room_id = chat_message.common.roomId
                user_id = chat_message.user.id
                user_level = message_utils.get_user_level(chat_message.user)
                question = chat_message.content
                answer = answer
                ins_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(chat_message.eventTime))

                sql = f"INSERT INTO danmu_history (room_id,user_id,user_level,question,answer,time) " \
                      f"VALUES ('{room_id}','{user_id}',{user_level},'{question}','{answer}','{ins_time}')"
                self.cursor.execute(sql)
                self.conn.commit()
        except Exception as e:
            logging.info("！！！插入弹幕数据失败！！！")
            traceback.print_exc()
            logging.info(chat_message)


# data_dir_path = "./conf/data_dir.ini"
# data_dir_conf = configparser.ConfigParser()
# data_dir_conf.read(data_dir_path, encoding="UTF-8")
# db_dir = data_dir_conf.get("parameter", "DBFile")

db = LiteDb()
db.open_db(db_config['parameter']['DBFile'])
