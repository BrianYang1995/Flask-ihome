# coding:utf-8

# 图片验证码保存到redis中的有效期
IMAGE_CODE_REDIS_EXPIRES = 180


# 短信验证码保存到redis中的有效期
SMS_CODE_REDIS_EXPIRES = 300

# 短信验证码60s内禁止请求，
SMS_SEND_TIME = 60

# 登录错误允许次数
LOGIN_ERR_AMOUNT = 5

# 多次登录错误禁止登录时间
FRODID_LOGIN_TIME = 600

# 七牛域名
QINIU_ADDR = 'http://pdw7yhwoi.bkt.clouddn.com/'

# 每页显示数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 列表页面缓存时间
HOUSE_LIST_EXPIRE_TIME = 7200
