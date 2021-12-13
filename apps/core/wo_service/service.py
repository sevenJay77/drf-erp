import time
import hashlib
import requests
import json

from core.utils.redis_client import RedisClientInstance
from config.config import WOModuleConfig
from core.framework.v_exception import VException

import logging

logger = logging.getLogger("django")

def get_wo_token_by_cache():
    access_token = ""
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'wo_service:access_token'
        cache_value = redis_client.get_by_name(cache_key)
        if cache_value:
            access_token = cache_value.decode()
        if not access_token:
            # 重新获取token
            access_token = get_wo_token()
            # 20个小时过期
            expire_in = 20 * 60 * 60
            redis_client.single_set_string_with_expire_time(cache_key, 'second', expire_in, access_token)
    except Exception as e:
        logger.error("wo token cache 获取异常， error:{}".format(e))
        raise VException(500, "WO 服务器正忙，请稍后再试")
    return access_token


def get_wo_token():
    app_id = WOModuleConfig.app_id
    access_key = WOModuleConfig.access_key
    app_secret = WOModuleConfig.access_secret
    token_url = "http://wo-api.uni-ubi.com/v1/{}/auth".format(app_id)

    try:
        # 签名加密
        timestamp = str(int(time.time() * 1000))
        hl = hashlib.md5()
        sign_str = "{}{}{}".format(access_key, timestamp, app_secret)
        hl.update(sign_str.encode("utf-8"))
        sign = hl.hexdigest()
        # 头部信息
        headers = {
            'appKey': access_key,
            'timestamp': timestamp,
            'sign': sign
        }
        res = requests.get(url=token_url, headers=headers).json()
        deal_wo_response(res)
        access_token = res['data']
    except VException as v_e:
        raise v_e
    except Exception as e:
        logger.error("wo token 获取异常， error:{}".format(e))
        raise VException(500, "WO token 接口异常")

    return access_token


# 删除Token
def delete_wo_token():
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'wo_service:access_token'
        redis_client.delete_by_name(cache_key)
    except Exception as e:
        logger.error("wo token cache 刷新异常， error:{}".format(e))
        raise VException(500, "WO 服务器正忙，请稍后再试")


# WO 注册用户
def register_wo_user(name):
    api_url = "http://wo-api.uni-ubi.com/v2/admit/create"
    token = get_wo_token_by_cache()
    params = {
        'name': name
    }
    # 头部信息
    headers = {
        "Content-Type": "application/json",
        'projectGuid': WOModuleConfig.app_id,
        'token': token
    }
    try:
        res = requests.post(url=api_url, data=json.dumps(params), headers=headers).json()
        logger.info("wo res : {}".format(res))
        deal_wo_response(res)
        admit_guid = res['data']['admitGuid']
    except VException as v_e:
        raise v_e
    except Exception as e:
        logger.error("wo 注册用户接口异常， error:{}".format(e))
        raise VException(500, "WO 注册用户接口异常")

    return admit_guid


# WO 删除用户
def delete_wo_user(admit_guid):
    api_url = "http://wo-api.uni-ubi.com/v2/admit/delete"
    token = get_wo_token_by_cache()
    params = {
        'admitGuids': admit_guid
    }
    # 头部信息
    headers = {
        "Content-Type": "application/json",
        'projectGuid': WOModuleConfig.app_id,
        'token': token
    }
    try:
        res = requests.post(url=api_url, data=json.dumps(params), headers=headers).json()
        logger.info("wo delete : {}".format(res))
        deal_wo_response(res)
    except VException as v_e:
        raise v_e
    except Exception as e:
        logger.error("wo 删除用户接口异常， error:{}".format(e))
        raise VException(500, "WO 删除用户接口异常")


# WO 用户列表
def get_wo_list():
    api_url = "http://wo-api.uni-ubi.com/v2/admit/page"
    token = get_wo_token_by_cache()
    params = {
        "index": 0,
	    "length": 99,
    }
    # 头部信息
    headers = {
        "Content-Type": "application/json",
        'projectGuid': WOModuleConfig.app_id,
        'token': token
    }
    try:
        res = requests.post(url=api_url, data=json.dumps(params), headers=headers).json()
        logger.info("wo get list: {}".format(res))
        deal_wo_response(res)
        data = res['data']['content']
    except VException as v_e:
        raise v_e
    except Exception as e:
        logger.error("wo 用户列表接口异常， error:{}".format(e))
        raise VException(500, "WO 用户列表接口异常")
    return data


# 处理返回值
def deal_wo_response(res):
    res_code = res['code']
    if res_code == 'WO_EXP-1203':
        # token 不合法， 删除token
        delete_wo_token()
        raise VException(500, 'WO凭证失效，请刷新后重试')

    if res_code != "WO_SUS1000":
        raise VException(500, "WO 接口异常")
