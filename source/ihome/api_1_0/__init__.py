# coding:utf-8

from flask import Blueprint


# 创建蓝图
api = Blueprint('api_1_0', __name__)

# 导入蓝图视图函数
from . import validate_code, passport, profile, my, house, order
