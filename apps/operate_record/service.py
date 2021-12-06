import datetime
import json
import time
from django.db import transaction
from core.framework.v_exception import VException
from core.utils.redis_client import RedisClientInstance
from operate_record.models import NotifyMessage
from config.config import CommonConfig

import logging

logger = logging.getLogger("django")


# 推荐发送
def notify_ws(message):
    # 添加记录
    try:
        notify = NotifyMessage()
        notify.user_id = message['user_id']
        notify.tenant_id = message['tenant_id']
        notify.title = message['title']
        notify.module = message['module']
        notify.record_sign = message['record_sign']
        notify.save()
        # 加入通知队列
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = CommonConfig.consumer_key
        redis_client.insert_to_list_tail(cache_key, json.dumps(message))

    except Exception as e:
        logger.error("send notify error {}".format(e))
        raise VException(500, "服务器繁忙，请稍后再试")
