# coding:utf-8

"""工程初始化信息"""
import redis
import logging
from logging.handlers import RotatingFileHandler

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from flask import Flask

from config import config_map
from ihome.utils.common import ReConverter
from ihome.libs.CCPSDK.SendTemplateSMS import CCP


# 数据库
db = SQLAlchemy()

# redis存储
redis_store = None

# 日志信息
# 设置记录日志的等级
logging.basicConfig(level=logging.DEBUG)
# 创建日志记录器，指明日志保存路径、每个日志的最大容量、保存日志文件的数量上限
file_log_handler = RotatingFileHandler('logs/log', maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式             日志级别         输入日志信息文件名  行数     日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志器
logging.getLogger().addHandler(file_log_handler)

# 采用工厂模式创建api
def create_app(config_name):
    """
    创建flask应用对象
    :param config_name: str  配置模式名字 ("develop"，"product")
    :return: app 实例对象
    """

    app = Flask(__name__)

    # api的flask配置信息
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 数据库注册app
    db.init_app(app)

    # 创建redis缓存连接对象
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # session数据存储
    Session(app)

    # CSRF验证组件
    CSRFProtect(app)

    # 添加自定转换器
    app.url_map.converters['re'] = ReConverter

    # 导入蓝图
    from ihome import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix='/api/v1.0')

    # 静态页面蓝图
    from ihome.web_html import html
    app.register_blueprint(html)



    return app

