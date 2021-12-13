import threading
import json
import datetime
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from permcontrol.models import VerifyCode
from core.utils.redis_client import RedisClientInstance
from config.config import AliModuleConfig, SafeModuleConfig
from core.framework.v_exception import VException, KException

import logging
logger = logging.getLogger("django")

# 阿里短信平台
class AliSmsClient():
    def __init__(self):
        logger.info(" ================= ali sms init =====================")
        self.client = AcsClient(AliModuleConfig.access_key_id, AliModuleConfig.access_secret)
        self.sign_name = AliModuleConfig.sms_sign_name
        self.register_template_code = AliModuleConfig.register_template_code
        self.login_template_code = AliModuleConfig.login_template_code
        self.forget_password_code = AliModuleConfig.forget_password_code
        self.invite_template_code = AliModuleConfig.invite_template_code

    def send_verify_sms(self, mobile, ip, event, random_code, extra=None):
        time_now = datetime.datetime.now()
        ip_count = VerifyCode.objects.filter(mobile=mobile,
                                             ip=ip,
                                             created_time__day=time_now.day).count()
        if ip_count > SafeModuleConfig.ip_verify_limit:
            raise VException(500, "发送太频繁")

        # 校验 1分钟之内只能发一次
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'sms_send_cache:{}:{}'.format(event, mobile)
        flag = redis_client.singe_setnx_string(cache_key, time.time(), 60)
        if not flag:
            raise VException(500, '一分钟内已发过验证码')
        try:
            # 发送验证码
            self.ali_server_send(mobile, event, random_code, extra)
            # 记录入库
            send_record = VerifyCode()
            send_record.mobile = mobile
            send_record.ip = ip
            send_record.event = event
            send_record.code = random_code
            send_record.save()
        except Exception as e:
            redis_client.delete_by_name(cache_key)
            raise e




    def ali_server_send(self, mobile, event, code, extra=None):
        request = CommonRequest()
        # 基础配置
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')
        # 短信配置
        request.add_query_param('PhoneNumbers', mobile)
        request.add_query_param('SignName', self.sign_name)
        if event == 'register':
            request.add_query_param('TemplateCode', self.register_template_code)
            request.add_query_param('TemplateParam', "{\"code\":\"%s\"}"%(code))

        elif event == 'login':
            request.add_query_param('TemplateCode', self.login_template_code)
            request.add_query_param('TemplateParam', "{\"code\":\"%s\"}"%(code))

        elif event == 'forget_password':
            request.add_query_param('TemplateCode', self.forget_password_code)
            request.add_query_param('TemplateParam', "{\"code\":\"%s\"}"%(code))

        elif event == 'invite_staff':
            request.add_query_param('TemplateCode', self.invite_template_code)
            request.add_query_param('TemplateParam', "{\"code\":\"%s\"}" % (code))
        else:
            raise VException(500, '模板错误')

        try:
            response = self.client.do_action(request)
            response = json.loads(response.decode())
            resp_code = response.get("Code")
        except Exception as e:
            logger.error('ali sms send error {}'.format(e))
            raise VException(500, '服务器繁忙，请稍后再试')

        if resp_code != "OK":
            logger.error("ali sms send code {}".format(resp_code))
            raise VException(500, '发送失败，请稍后再试')


class AliSmsClientInstance(object):
    # 线程锁
    _instance_lock = threading.Lock()

    def __init__(self, *args,**kwargs):
        pass

    @classmethod
    def get_storage_instance(cls):
        if not hasattr(AliSmsClientInstance,'_instance'):
            with AliSmsClientInstance._instance_lock:
                    AliSmsClientInstance._instance = AliSmsClient()
        return AliSmsClientInstance._instance
