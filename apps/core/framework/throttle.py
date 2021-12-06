import json
import time
import logging

from rest_framework.throttling import BaseThrottle
from core.utils.functions import get_ip_address
from config.config import SafeModuleConfig
from core.utils.redis_client import RedisClientInstance
from core.framework.v_exception import VException, KException
from app_edition.models import AppEdition


logger = logging.getLogger("django")



# 登录频率限制（缓存redis）
class UserRateThrottle(BaseThrottle):

    def __init__(self):
        self.redis_client = RedisClientInstance.get_storage_instance()
        self.rates = {
            'anon': SafeModuleConfig.anon_time_request,
            'user': SafeModuleConfig.user_time_request
        }
        self.requests_limit = self.parse_rate(self.rates)
        self.history = []


    def parse_rate(self, rates):
        requests_limit = {}

        for scope, rate in rates.items():
            num, period = rate.split('/')
            num_requests = int(num)
            duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
            requests_limit[scope] = {
                'num_requests': num_requests,
                'duration': duration
            }

        return requests_limit


    def allow_request(self, request, view):
        '''
        日志记录访问
        '''
        try:
            request_body = json.loads(request.body)
        except:
            request_body = dict()
        if request.method == 'GET':
            request_body.update(dict(request.GET))
        else:
            request_body.update(dict(request.POST))
        logger.info("url: {}, method: {}, body: {}".format(request.get_full_path(), request.method, json.dumps(request_body)))

        # 访问频率控制
        try:
            ident_ip = get_ip_address(request)
            user = request.user
            if user:
                # 验证用户
                scope = 'user'
                ident = user.id
                duration = self.requests_limit['user']['duration']
                num_requests = self.requests_limit['user']['num_requests']

            else:
                # 匿名用户
                scope = 'anon'
                ident = ident_ip
                duration = self.requests_limit['anon']['duration']
                num_requests = self.requests_limit['anon']['num_requests']

            # APP校验版本号
            app_code = request.META.get('HTTP_VERSION_CODE', None)
            if app_code:
                current_version = AppEdition.objects.filter(edition_code=app_code,
                                                            is_delete=0).first()
                if not current_version:
                    raise VException(500, '当前APP已失效，请卸载后重新下载')

                # 审核中的APP忽略升级
                if current_version.status == 2:
                    '''
                    APP请求 校验是否强制更新
                    当前版本号向上寻找，查找是否有已上架的强制更新
                    '''
                    last_code = AppEdition.objects.filter(status=2,
                                                          forced_update=1,
                                                          edition_code__gt=app_code).first()
                    if last_code:
                        raise VException(506, 'APP有新版本需要升级')

            # 缓存key
            cache_key = 'throttle:{}:{}'.format(scope, ident)

            # 获取访问记录
            self.history = []
            cache_history = self.redis_client.get_by_name(cache_key)
            if cache_history:
                self.history = json.loads(cache_history)

            # 当前时间
            self.now = time.time()
            while self.history and self.history[-1] <= self.now - duration:
                self.history.pop()
            # 请求总数
            if len(self.history) >= num_requests:
                logger.error("访问太频繁，请稍后访问")
                raise VException(500, '访问太频繁，请稍后访问')

            # 头部插入访问记录
            self.history.insert(0, self.now)

            self.redis_client.single_set_string_with_expire_time(cache_key, "second", duration, json.dumps(self.history))

            return True

        except VException as v_exc:
            raise v_exc
        except Exception as e:
            logger.error("operate log error {}".format(e))
            raise VException(500,  '服务器正忙，请稍后再试')
