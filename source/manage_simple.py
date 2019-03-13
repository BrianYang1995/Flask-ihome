# coding:utf-8

import redis

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect

app = Flask(__name__)


# 配置信息
class Config(object):
    """配置信息"""
    DEBUG = True

    SECRET_KEY = 'HANDINN+JIFJ?kl'

    # 数据库设置
    SQLALCHEMY_DATABASE_URI = 'mysql://root@1127.0.0.1:3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask_session 配置
    SESSION_TYPE = 'redis' # session存储数据库
    SESSION_USE_SIGNER = True # session混淆处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT) # session的redis存储
    PERMANENT_SESSION_LIFETIME = 3600*24*7 # session有效期




app.config.from_object(Config)

# 数据库
db = SQLAlchemy(app)

# 创建redis缓存连接对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# session数据存储
Session(app)

# CSRF验证组件
CSRFProtect(app)




@app.route('/index')
def index():
    return "index page"


if __name__ == '__main__':
    app.run()

