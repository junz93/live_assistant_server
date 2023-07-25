#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/4/21 14:07
# @Author  : zhongzhilai
# @File    : utils.py
# @Description :

import re
import Levenshtein


def filter_emoji(text, restr=""):
    try:
        res = re.compile(u'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]')
        return res.sub(restr, text)
    except Exception as e:
        print(f"过滤emoji表情出错，输入：{text}\n异常：{e}")
        return ""


def filer_biaoqing(text, restr=""):
    try:
        return re.sub(u"\\[.*?]", restr, text)
    except Exception as e:
        print(f"过滤普通表情出错，输入：{text}\n异常：{e}")
        return ""


def is_contains_chinese(text):
    for _char in text:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False


def filer_nickname(user_nickname):
    def dashrepl(matchobj):
        return matchobj.group(0)[:2] + matchobj.group(0)[2:][-4:]
    # 过滤默认用户名（用户+数字）
    user_nickname = re.sub('用户\d*$', dashrepl, user_nickname)
    return user_nickname


def str_repeat(s1, s2, threshold):
    """
    判断字符串是否相似：编辑距离占最长字符串比例
    """
    dis = Levenshtein.distance(s1, s2)
    if 1 - dis / max(len(s1), len(s2)) >= threshold:
        return True
    else:
        return False


def get_user_level(user_message):
    user_level = 0
    for badgeImageList in user_message.BadgeImageList:
        if badgeImageList.imageType == 1:
            user_level = badgeImageList.content.level
            break
    return user_level


def get_fans_level(user_message):
    fans_level = 0
    for badgeImageList in user_message.BadgeImageList:
        if badgeImageList.imageType == 7:
            fans_level = badgeImageList.content.level
            break
    return fans_level


if __name__ == '__main__':
    s = "python is 👍"
    print(filter_emoji(s))
    s = "用户23232321"
    print(filer_nickname(s))
