# coding:utf-8
import random
from flask import current_app, jsonify, make_response, request

from ihome.libs.CCPSDK.SendTemplateSMS import CCP
from ihome.api_1_0 import api
from ihome import redis_store
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome import constants
from ihome.models import User

# GET  /api/v1.0/image_codes/<image_code_id>
@api.route('/image_codes/<image_code_id>')
def image_code(image_code_id):
    """
    提供图片验证码
    :param image_code_id: str 前端生成的验证码id
    :return: 正常：验证码图片，异常：Json字符串
    """
    # 业务逻辑处理
    # 生成验证码
    name, text, image_data = captcha.generate_captcha()

    # 保存到redis中，数据类型：字符串
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(u'保存验证码失败')
        return jsonify(errcode=RET.DBERR, errmsg='保存验证码图片失败')
    # 返回
    resp = make_response(image_data)
    # 修改请求头
    resp.headers['Content-Type'] = 'image/jpg'
    return resp

# GET  /api/v1.0/sms_codes/<mobile>
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def sms_code(mobile):
    """获取短信验证码"""
    # 接收数据
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    # 校验数据
    # 验证码数据是否存在
    if not all([image_code, image_code_id]):
        return jsonify(errcode=RET.DATAERR, errmsg='验证码信息不全')

    try:
        redis_code = redis_store.get('image_code_%s' % image_code_id)
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmag='数据库信息错误')

    if redis_code is None:
        return jsonify(errcode=RET.NODATA, errmsg='验证码过期')
    elif image_code.lower() != redis_code.lower():
        return jsonify(errcode=RET.DATAERR, errmag='验证码错误')

    # 业务逻辑处理
    # 查询用户手机是否存在
    try:
        if User.query.filter_by(mobile=mobile).first():
            return jsonify(errcode=RET.DATAEXIST, errmsg='手机号已被注册')
    except Exception as e:
        current_app.logger.error(e)

    # 短信验证码
    sms_codes = '%06d' % random.randint(0, 999999)

    # 将短信验证码存入redis
    try:
        if redis_store.get('mobile_%s' % mobile) is None:
            redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_codes)
            redis_store.setex('mobile_%s' % mobile, constants.SMS_SEND_TIME, 1)
        else:
            return jsonify(errcode=RET.DATAEXIST, errmsg='请求过于频繁，稍后再尝试')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmag='数据库信息错误')

    # 发送信息
    try:
        # 发送短信
        sms_sender = CCP()
        resp = sms_sender.sendTemplateSMS(mobile, [sms_codes, 5], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.THIRDERR, errmsg='第三方系统错误')

    # 返回
    if resp:
        return jsonify(errcode=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errcode=RET.THIRDERR, errmsg='第三方系统错误')