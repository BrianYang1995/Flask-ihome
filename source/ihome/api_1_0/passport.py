# coding:utf-8

import re

from flask import request, jsonify, current_app, session

from . import api
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import User
from ihome import constants


# 注册
#  POST /api/v1.0/users
@api.route('/users', methods=['POST'])
def register():
    """用户注册处理"""
    # 接收参数
    # 获取json数据，返回字典
    req_data = request.get_json()

    mobile = req_data.get('mobile')
    sms_code = req_data.get('sms_code')
    password = req_data.get('password')
    cpassword = req_data.get('cpassword')

    # 校验参数
    if not all([mobile, sms_code, password, cpassword]):
        return jsonify(errcode=RET.PARAMERR, errmsg='数据不完整')

    # 校验手机号
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errcode=RET.PARAMERR, errmsg='手机号格式错误')

    # 两次密码是否相同
    if password != cpassword:
        return jsonify(errcode=RET.PARAMERR, errmsg='两次密码不相同')

    # 短信验证码是否正确
    try:
        redis_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='读取验证码数据库错误')

    if redis_sms_code is None:
        return jsonify(errcode=RET.DATAERR, errmsg='短信验证码过期')

    if sms_code != redis_sms_code:
        return jsonify(errcode=RET.DATAERR, errmsg='短信验证码错误')

    # 手机号是否注册
    user = User(name=mobile, mobile=mobile)
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DATAERR, errmsg='手机号已被注册')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库异常')

    # 业务逻辑处理
    session['user_id'] = user.id
    session['username'] = mobile
    session['mobile'] = mobile

    # 返回
    return jsonify(errcode=RET.OK, errmsg='注册成功')


# 登录验证视图
# POST /api/v1.0/session
@api.route('/session', methods=['POST'])
def login():
    """登录验证视图函数"""
    # 接收参数
    obj_dict = request.get_json()

    mobile = obj_dict.get('mobile')
    password = obj_dict.get('password')
    user_ip = request.remote_addr

    # 校验数据完整性
    if not all([mobile, password]):
        return jsonify(errcode=RET.DATAERR, errmsg='登录数据不完整')

    # 校验手机号格式
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errcode=RET.DATAERR, errmsg='手机号格式错误')

    # 判断登录错误次数，次数超过上线禁止登录
    try:
        try_num = redis_store.get('login_err_num_%s' % user_ip)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.LOGINERR, errmsg='请稍后再试')

    if try_num and int(try_num) > constants.LOGIN_ERR_AMOUNT:
        return jsonify(errcode=RET.LOGINERR, errmsg='登录错误次数过多，请稍后再试')

    # 判用户名和密码是否正确
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DATAERR, errmsg='获取用户信息失败')

    # 如果错误记录错误次数
    if not user or not user.check_password(password):
        redis_store.incr('login_err_num_%s' % user_ip)
        redis_store.expire('login_err_num_%s' % user_ip, constants.FRODID_LOGIN_TIME)
        return jsonify(errcode=RET.LOGINERR, errmsg='用户名或密码错误')

    # 记录session信息
    session['user_id'] = user.id
    session['username'] = user.name
    session['mobile'] = user.mobile
    print (user.real_name)
    if user.real_name:

        session['is_auth'] = 1
    else:
        session['is_auth'] = 0
    # 返回
    return jsonify(errcode=RET.OK, errmsg='登录成功')


# 登录判断
# GET /api/v1.0/session
@api.route('/session', methods=['GET'])
def check_login():
    """判断用户是否登录"""
    # 查看session中是否有username
    name = session.get('username')
    if name:
        return jsonify(errcode=RET.OK, errmsg=name)
    else:
        return jsonify(errcode=RET.DATAERR, errmsg='用户未登录')


# 登出
# DELETE /api/v1.0/session
@api.route('/session', methods=['DELETE'])
def logout():
    """用户登出视图函数"""
    session.clear()
    return jsonify(errcode=RET.OK, errmsg='成功退出')
