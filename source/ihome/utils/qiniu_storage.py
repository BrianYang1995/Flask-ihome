# coding:utf-8

from qiniu import Auth, put_data, etag

# 需要填写你的 Access Key 和 Secret Key
access_key = 'JNXWnfjPbIibGFEIVYKddUgvI0cLBEVwWFxRxZPk'
secret_key = '_XvtKMz-cQqdXDGPoMC68sFbwAxTvv6DYgxI_w_4'


def qiniu_upload(data):
    """七牛上传文件封装"""

    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, data)

    if info.status_code == 200:
        return ret.get('key')
    else:
        return 0

    # print('**********',info)
    # print(ret)


if __name__ == '__main__':

    with open('./1.jpg', 'rb') as f:
        data = f.read()
        qiniu_upload(data)
