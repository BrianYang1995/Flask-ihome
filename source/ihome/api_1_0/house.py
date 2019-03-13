# coding:utf-8

from flask import request, jsonify, g, current_app, session
from . import api
from ihome.models import House, Area, Facility, HouseImage, Order
from ihome.utils.response_code import RET
from ihome.utils.common import logged
from ihome import db, redis_store
from ihome.utils.qiniu_storage import qiniu_upload
from ihome import constants
from datetime import datetime
import json

# GET /api/v1.0/area
@api.route('/area', methods=['GET'])
def area():
    """获取区域信息"""
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库查询失败')

    area_list =[]
    for area in areas:
        ret = area.get_area()
        area_list.append(ret)

    return jsonify(errcode=RET.OK, errmsg='Ok', data=area_list)


# POST /api/v1.0/house/info
@api.route('/house/info', methods=['POST'])
@logged
def new_house():
    """添加房源"""
    user_id = g.user_id

    house_info = request.get_json()
    title = house_info.get('title')
    price = house_info.get('price')
    area_id = house_info.get('area_id')
    address = house_info.get('address')
    room_count = house_info.get('room_count')
    acreage = house_info.get('acreage')
    unit = house_info.get('unit')
    capacity = house_info.get('capacity')
    beds = house_info.get('beds')
    deposit = house_info.get('deposit')
    min_days = house_info.get('min_days')
    max_days = house_info.get('max_days')

    # 数据完整性
    if not all([title, area_id, price, address, room_count, acreage,unit,capacity,
            beds, deposit, max_days, min_days]):
        return jsonify(errcode=RET.DATAERR, errmsg='数据不完整')

    # 转换数据
    try:
        price = float(price)*100
        room_count = int(room_count)
        acreage = float(acreage)
        capacity = int(capacity)
        deposit = float(deposit)*100
        min_days = int(min_days)
        max_days = int(max_days)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DATAERR, errmsg='数据格式不正确')

    # 城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库查询错误')

    if area is None:
        return jsonify(errcode=RET.DATAERR, errmsg='城区不存在')

    house = House(user_id=int(user_id), area_id=int(area_id),
                  title=title, price=price,
                  address=address, room_count=room_count,
                  acreage=acreage, unit=unit, capacity=capacity,
                  beds=beds, deposit=deposit, min_days=min_days,
                  max_days=max_days)

    # 接收设施信息
    facilities = house_info.get('facility')

    if facilities:
        try:
            facility_list = Facility.query.filter(Facility.id.in_(facilities)).all()
            house.facilities = facility_list
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errcode=RET.DBERR, errmsg='数据库查询错误')

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errcode=RET.OK, errmsg='Ok', data={'house_id': house.id})


# POST /api/v1.0/house/image
@api.route('/house/image', methods=['POST'])
def set_house_image():
    """接收房屋信息图片"""
    # 接收数据
    house_image = request.files.get('house_image')
    house_id = request.form.get('house_id')
    print("**************",house_id)
    # 校验数据
    if house_image is None:
        return jsonify(errcode=RET.NODATA, errmsg='数据不全')
    # 图片上传
    try:
        ret = qiniu_upload(house_image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.THIRDERR, errmsg='第三方错误')

    if ret:
        image_name = ret
    else:
        return jsonify(errcode=RET.NODATA, errmsg='保存失败')

    # 设置index图片
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库错误')


    if house.index_image_url == '':
        house.index_image_url = image_name

    # 保存图片信息到数据库
    try:
        house_img = HouseImage(house_id=house_id, url=image_name)
        db.session.add(house_img)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='数据库错误')
    # 返回
    url = constants.QINIU_ADDR + image_name
    return jsonify(errcode=RET.OK, errmsg='OK', data={'url': url})


# POST /api/v1.0/house/myhouse
@api.route('/house/myhouse')
@logged
def my_house():
    """我的房源列表"""
    # 获取个人实名身份信息
    if not session.get('is_auth'):
        return jsonify(errcode=RET.SESSIONERR, errmsg='未实名')

    # 获取用户id
    user_id = g.user_id
    # 获取用户房源信息
    try:
        house_li = House.query.filter_by(user_id=user_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询用户房源失败')

    if house_li is None:
        return jsonify(errcode=RET.NODATA, errmsg='未发布房源')

    # 生成房源信息列表
    houses = []
    for house in house_li:
        house_info = house.to_basic_dict()
        houses.append(house_info)

    return jsonify(errcode=RET.OK, errmsg='OK', data={'houses': houses})


# GET /v1.0/house/index
@api.route('/house/index')
def index_house_image():
    """主页房屋轮播图"""
    # 获取用户房源信息
    try:
        house_li = House.query.limit(4).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询房源失败')

    if house_li is None:
        return jsonify(errcode=RET.NODATA, errmsg='未发布房源')

    # 生成房源信息列表
    houses = []
    for house in house_li:
        house_info = house.to_basic_dict()
        houses.append(house_info)

    return jsonify(errcode=RET.OK, errmsg='OK', data={'houses': houses})


# GET /api/v1.0/house/detail
@api.route('/house/detail')
def house_detail():
    """房源详情"""
    # 获取房源id
    house_id = request.args.get('house_id')

    # house_id是否存在
    try:
        house = House.query.get(house_id)
        facilities = house.facilities
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库错误')

    if house is None:
        return jsonify(errcode=RET.NODATA, errmsg='无该房源')

    # 获取房源图片
    try:
        images = HouseImage.query.filter_by(house_id=house_id).all()
    except Exception as e:
        current_app.logger.error(e)
        images = None

    # 房源图片列表
    image_list = []
    if images is None:
        image_url = {'url': constants.QINIU_ADDR + 'Fp6e7J6mj5tIm6sEP1TzhLj-xN7w'}
        image_list.append(image_url)
    else:
        for image in images:
            image_list.append(image.get_img_url())

    # 房源信息
    house_info = house.to_basic_dict()
    # 设施项，存放在列表中
    facility_list = house.facilities
    facilities = []
    for facility in facility_list:
        facilities.append(facility.id)

    house_info['facilities'] = facilities

    # 评论信息
    try:
        orders = Order.query.filter_by(house_id=house_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库错误')

    # 评论信息存放列表
    comment_list = []
    if orders:
        for order in orders:
            comment = order.comment_info()
            comment_list.append(comment)

    house_info['comments'] = comment_list

    user_id = session.get('user_id', None)

    return jsonify(errcode=RET.OK, errmsg='OK', data={'images':image_list, 'house_info': house_info, 'user_id': user_id})


# GET /api/v1.0/house/search?sd=&ed=&aid=&sk=&p=
@api.route('/house/search')
def search():
    """搜索页面数据"""
    # 接收参数
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    area_id = request.args.get('aid')
    sort_type = request.args.get('sk')
    page = request.args.get('p')

    # 参数合理性
    # 时间合理
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DATAERR, errmsg='日期参数有误')

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errcode=RET.DATAERR, errmsg='区域信息有误')

    # 处理页数
    if page:
        try:
            page = int(page)
        except Exception as e:
            current_app.logger.error(e)
            page = 1
    else:
        page = 1

    # 从缓存中读取数据
    redis_key = 'house_list_%s_%s_%s_%s' % (start_date, end_date, area_id, sort_type)

    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        resp_json = None
        current_app.logger.error(e)

    if resp_json:
        return resp_json, 200, {'Content-Type': 'application/json'}


    # 查询条件参数容器
    filter_params = []

    # 填充过滤参数
    # 时间
    conflict_orders = None
    try:
        if start_date and end_date:
            conflict_orders = Order.query.filter(Order.begin_date<=end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='查询数据库失败')

    if conflict_orders:
        # 从订单中提取冲突的房屋id
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # 如果房屋id不为空，添加查询条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域id
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 补充排序条件
    if sort_type == 'booking':
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_type == 'price-inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_type == 'price-des':
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    try:
        # 处理分页                        页码                    页面容量                          关闭错误输出
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RET.DBERR, errmsg='获取房屋信息失败')

    # 获取页面数据
    house_list = page_obj.items
    houses = []
    for house in house_list:
        houses.append(house.to_basic_dict())

    total_page = page_obj.pages

    # return jsonify(errcode=RET.OK, errmsg='OK', data={'total_page': total_page, 'houses': houses, 'page':page})
    resp = dict(errcode=RET.OK, errmsg='OK', data={'total_page': total_page, 'houses': houses, 'page':page})
    resp_json = json.dumps(resp)

    # 缓存数据
    if page <= total_page:
        try:
            # redis_store.hset(redis_key, page, resp)
            # redis_store.expire(redis_key, constants.HOUSE_LIST_EXPIRE_TIME)

            # 创建管道对象，一次可执行多个语句
            redis_pipeline = redis_store.pipeline()

            # 开启多个语句的记录
            redis_pipeline.multi()

            redis_pipeline.hset(redis_key, page, resp_json)
            redis_pipeline.expire(redis_key, constants.HOUSE_LIST_EXPIRE_TIME)

            #执行语句
            redis_pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {'Content-Type': 'application/json'}







































