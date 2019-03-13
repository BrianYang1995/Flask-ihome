# coding:utf-8

from flask import request, current_app, jsonify, g, session

from . import api
from ihome import db
from ihome.utils.common import logged
from ihome.utils.response_code import RET
from ihome.utils.qiniu_storage import qiniu_upload
from ihome.constants import QINIU_ADDR
from ihome.models import User


# POST /api/v1.0/avatar
@api.route('/avatar', methods=['POST'])
@logged
def set_avatar():
    """设置用户头像"""
    # 接收数据
    file_name = request.files.get('avatar')

    # 校验数据
    if not file_name:
        return jsonify(errcode=RET.DATAERR, errmsg='上传数据为空')

    # 业务逻辑处理
    # 保存到七牛
    try:
        rest = qiniu_upload(file_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.THIRDERR, errmsg='保存失败1')

    # 保存到数据库
    if rest:
        try:
            print rest
            User.query.filter_by(id=g.user_id).update({"avatar_url": rest})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errcode=RET.THIRDERR, errmsg='保存失败2')
        url = QINIU_ADDR + rest
    else:
        return jsonify(errcode=RET.THIRDERR, errmsg='保存失败3')

    # 返回
    return jsonify(errcode=RET.OK, errmsg='上传成功', data=url)


# GET /api/v1.0/avatar
@api.route('/profile', methods=['GET'])
@logged
def profile():
    """为前端提供头像地址"""
    # 获取用户id
    user_id = g.user_id

    # 获取用户头像名字
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')
    print (user)


    # 拼凑url地址
    avatar = user.avatar_url
    if avatar is None:
        avatar_url = QINIU_ADDR + 'FsFl5J_EzdibRC5ayelfVy9sKfZ0'
    else:
        avatar_url = QINIU_ADDR + avatar
    # 获取用户名
    user_name = user.name

    return jsonify(errcode=RET.OK, errmsg='获取用户头像地址成功', data={'avatar': avatar_url, 'name': user_name})


# POST /api/v1.0/name
@api.route('/name', methods=['PUT'])
@logged
def change_name():
    """修改用户名"""
    # 获取用户id
    user_id = g.user_id

    # 获取更新用户名
    user_name = request.get_json().get('name')

    # 更新用户名
    try:
        User.query.filter_by(id=user_id).update({'name': user_name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='用户名已存在')

    session['username'] = user_name

    return jsonify(errcode=RET.OK, errmsg='更新用户名成功')
















