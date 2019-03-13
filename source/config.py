# coding:utf-8

import redis


# 配置信息
class Config(object):
    """基本配置信息"""

    SECRET_KEY = 'HANDINN+JIFJ?kl'

    # 数据库设置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Yang-9110@127.0.0.1:3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask_session 配置
    SESSION_TYPE = 'redis' # session存储数据库
    SESSION_USE_SIGNER = True # session混淆处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT) # session的redis存储
    PERMANENT_SESSION_LIFETIME = 3600*24*7 # session有效期


class DevelopmentConfig(Config):
    """开发环境配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map = {
    'develop': DevelopmentConfig,
    'product': ProductionConfig,
}