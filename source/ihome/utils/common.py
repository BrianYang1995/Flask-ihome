# coding:utf-8

from response_code import RET
from werkzeug.routing import BaseConverter
from functools import wraps

from flask import session, jsonify, g
# 定义一个正则转换器
class ReConverter(BaseConverter):
    """正则交换器"""
    def __init__(self, url_map, regex):
        # 调用父类初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


def logged(view_func):
    """登录判定装饰器"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id:
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errcode=RET.LOGINERR, errmsg='未登录')
    return wrapper