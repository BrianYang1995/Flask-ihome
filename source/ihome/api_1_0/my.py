# coding:utf-8

from flask import current_app, request, g, jsonify, session

from ihome.utils.response_code import RET
from . import api
from ihome import db
from ihome.utils.common import logged
from ihome.models import User
from ihome.constants import QINIU_ADDR


# GET /api/v1.0/my
@api.route('/my', methods=['GET'])
@logged
def my_info():
    """获取用户基本信息"""
    # 获取用户id
    user_id = g.user_id

    # 查询数据库
    try:
        user_info = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    # 返回的用户信息
    user_name = user_info.name
    user_mobile = user_info.mobile
    avatar = user_info.avatar_url
    if avatar is None:
        avatar_url = QINIU_ADDR + 'FsFl5J_EzdibRC5ayelfVy9sKfZ0'
    else:
        avatar_url = QINIU_ADDR + avatar

    # 判定是否登录
    if session.get('is_auth'):
        is_auth = 1
    else:
        is_auth = 0
    # 返回值
    return jsonify(errcode=RET.OK, errmsg='获取成功', data={'name': user_name, 'mobile': user_mobile, \
                                                        'avatar': avatar_url, 'is_auth': is_auth})


# GET /api/v1.0/auth
@api.route('/auth', methods=['GET'])
@logged
def get_auth():
    """获取实名认证信息"""
    user_id = g.user_id
    # 获取实名信息
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    real_name = user.real_name
    id_card = user.id_card

    return jsonify(errcode=RET.OK, errmsg='成功', data={'real_name': real_name, 'id_card': id_card})


# POST /api/v1.0/auth
@api.route('/auth', methods=['POST'])
@logged
def set_auth():
    """设置实名认证信息"""
    user_id = g.user_id
    # 接收实名信息
    user_info = request.get_json()

    real_name = user_info.get('real_name')
    id_card = user_info.get('id_card')

    # 校验参数
    if not all([real_name, id_card]):
        return jsonify(errcode=RET.NODATA, errmsg='用户信息不全')

    # 记录实名信息
    try:
        user = User.query.filter_by(id=user_id, real_name=None, id_card=None).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    try:
        if user is not None:
            user.real_name = real_name
            user.id_card = id_card
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库保存失败')

    session['is_auth'] = 1

    return jsonify(errcode=RET.OK, errmsg='成功', data={'real_name': real_name, 'id_card': id_card})

