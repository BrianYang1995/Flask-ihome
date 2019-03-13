# coding:utf-8

from CCPRestSDK import REST


# 主帐号
accountSid= '8aaf070865417618016555272fe30a11'

# 主帐号Token
accountToken= 'f1754197c41643159ec0be23698dbc7d'

# 应用Id
appId='8aaf0708654176180165552730300a17'

# 请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

# 请求端口
serverPort='8883'

# REST版本号
softVersion='2013-12-26'


# 发送短信类
class CCP(object):

    instance = None
    # 单例模式：__new__

    def __new__(cls):
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)

            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj
        return cls.instance


    # sendTemplateSMS(手机号码,内容数据:列表的形式,模板Id)
    def sendTemplateSMS(self, to, datas, tempId):
        """发送短信方法"""
        result = self.rest.sendTemplateSMS(to, datas, tempId)
        # 返回结果
        if result.get('statusCode') == '000000':
            res = 1
        else:
            res = 0
        print res
        return res


if __name__ == '__main__':

    send = CCP()
    send.sendTemplateSMS('17531425978', ['yang', 30], 1)

