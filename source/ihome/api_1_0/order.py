# coding:utf-8

from . import api
from ihome import db, redis_store
from ihome.utils.common import logged
from ihome.utils.response_code import RET
from flask import session, jsonify, request, current_app, g
from datetime import datetime
from ihome.models import House, Order


# GET /api/v1.0/check_login
@api.route('/check_login', methods=['GET'])
def checkLogin():
    """检查是否登录"""
    user_id = session.get('user_id', None)
    if not user_id:
        return jsonify(errcode=RET.LOGINERR, errmsg='用户未登录')
    return jsonify(errcode=RET.OK, errmsg='OK')


# POST /api/v1.0/order/info
@api.route('/order', methods=['POST'])
@logged
def get_order():
    """处理订单"""
    # 获取参数
    json_dict = request.get_json()

    house_id = json_dict.get('house_id')
    start_date_str = json_dict.get('start_date')
    end_date_str = json_dict.get('end_date')
    # 校验参数
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errcode=RET.DATAERR, errmsg='数据不全')

    # 日期是否正确
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DATAERR, errmsg='日期格式错误')

    if end_date < start_date:
        return jsonify(errcode=RET.DATAERR, errmsg='日期时间错误')

    # 房源信息
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    if not house:
        return jsonify(errcode=RET.DBERR, errmsg='房源不存在')

    # 订单中是否存在冲突
    try:
        orders = Order.query.filter(Order.house_id==house_id, Order.begin_date<=end_date, Order.end_date>=start_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    if orders:
        return jsonify(errcode=RET.PARAMERR, errmsg='订单冲突')

    # 业务处理
    days = int((end_date-start_date).days) + 1
    order_info = {
        'user_id': g.user_id,
        'house_id': house_id,
        'begin_date': start_date_str,
        'end_date': end_date_str,
        'days': days,
        'house_price': house.price,
        'amount': int(house.price)*int(days)
    }

    order = Order(use_id=g.user_id, house_id=house_id, \
                  begin_date=start_date, end_date=end_date, \
                  days=days, house_price=house.price,\
                  amount=int(house.price)*int(days))
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errcode=RET.OK, errmsg='OK')


# GET /api/v1.0/order/my
@api.route('/order/my', methods=['GET'])
@logged
def my_order():
    """订单信息"""
    role = request.args.get('role')
    user_id = g.user_id

    if role == 'custom': # 租户
        # 查询订单信息
        try:
            orders = Order.query.filter_by(use_id=user_id).order_by(Order.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errcode=RET.DBERR, errmsg='查询数据库错误')
    elif role == 'landlord':  # 房东
        try:
            houses = House.query.filter_by(user_id=user_id).all()
            house_ids = [house.id for house in houses]
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    else:
        return jsonify(errcode=RET.PARAMERR, errmsg='身份错误')


    # 用户订单列表
    order_list = []
    if orders:
        for order in orders:
            order_list.append(order.order_info())

    return jsonify(errcode=RET.OK, errmsg='OK', data={'orders': order_list})


# POST /api/v1.0/order/comment
@api.route('/order/comment', methods=['POST'])
@logged
def set_comment():
    """提交评论"""
    # 接收数据
    json_dict = request.get_json()
    order_id = json_dict.get('order_id')
    comment = json_dict.get('comment')

    # 校验参数
    if not all([order_id, comment]):
        return jsonify(errcode=RET.PARAMERR, errmsg='参数错误')

    if not comment:
        return jsonify(errcode=RET.DATAERR, errmsg='无评论信息')

    # 判断订单存在否
    try:
        order = Order.query.filter(Order.id==order_id, Order.status=='WAIT_COMMENT').first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库查询失败')

    if not order:
        return jsonify(errcode=RET.DATAERR, errmsg='数据不存在')

    # 保存评论数据
    try:
        order.update({'comment': comment})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errcode=RET.OK, errmsg='OK')


# POST /api/v1.0/order/accept
@api.route('/order/accept', methods=['POST'])
@logged
def accept_order():
    """房东接单"""
    json_dict = request.get_json()
    order_id = json_dict.get('order_id')
    user_id = g.user_id
    print order_id
    # 校验参数
    if not order_id:
        return jsonify(errcode=RET.NODATA, errmsg='无数据')

    try:
        order_id = int(order_id)
    except Exception as e:
        return jsonify(errcode=RET.PARAMERR, errmsg='订单id格式错误')

    # 业务处理
    # try:
    #     Order.query.filter_by(id=order_id, status='WAIT_ACCEPT').update({'status': 'WAIT_PAYMENT'})
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)
    #     return jsonify(errcode=RET.DBERR, errmsg='数据库保存失败')

    try:
        order = Order.query.filter_by(id=order_id, status='WAIT_ACCEPT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库失败')

    if not order or house.user_id != user_id:
        return jsonify(errcode=RET.NODATA, errmsg='数据处理失败')

    try:
        order.status = 'WAIT_PAYMENTPAID'
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库操作失败')
    return jsonify(errcode=RET.OK, errmsg='OK')


# POST /api/v1.0/order/reject
@api.route('/order/reject', methods=['POST'])
@logged
def reject_order():
    """房东接单"""
    json_dict = request.get_json()
    order_id = json_dict.get('order_id')
    reject_reason = json_dict.get('reject_reason')
    user_id = g.user_id


    # 校验参数
    if not all([order_id, reject_reason]):
        return jsonify(errcode=RET.NODATA, errmsg='数据不全')

    try:
        order_id = int(order_id)
    except Exception as e:
        return jsonify(errcode=RET.PARAMERR, errmsg='订单id格式错误')


    # 业务处理
    # try:
    #     Order.query.filter_by(id=order_id, status='WAIT_ACCEPT').update({'status': 'REJECTED', 'comment': reject_reason})
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)
    #     return jsonify(errcode=RET.DBERR, errmsg='数据库保存失败')

    try:
        order = Order.query.filter_by(id=order_id, status='WAIT_ACCEPT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库失败')

    if not order or house.user_id != user_id:
        return jsonify(errcode=RET.NODATA, errmsg='数据处理失败')

    try:
        order.status = 'REJECTED'
        order.comment = reject_reason
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库操作失败')


    return jsonify(errcode=RET.OK, errmsg='OK')

