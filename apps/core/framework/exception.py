from rest_framework.views import exception_handler
from django.core.exceptions import PermissionDenied
from core.framework.v_exception import VException, PermissException

from core.utils.functions import error_info, error_400_info
from core.framework.response import VResponse, PermissResponse

import logging

logger = logging.getLogger("django")

'''
自定义异常返回类
'''
def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    try:
        url = context['request'].get_full_path(),
    except:
        url = ""

    # 自定义返回码和错误提示
    if response:
        if response.status_code == 400:
            # 格式化错误信息
            detail = error_400_info(response.data)

        elif response.status_code == 401:
            detail = error_info(response.data, "认证错误")

        elif response.status_code == 403:
            detail = "没有访问权限"

        elif response.status_code == 404:
            detail = "请求对象不存在"

        elif response.status_code == 405:
            detail = "请求方法不被允许"

        elif response.status_code == 502:
            detail = "网络超时"

        else:
            detail = "服务器正忙,请稍后再试"

        response = VResponse(code=response.status_code, detail=detail, url=url)

    elif response is None:
        # 为空，自定义二次处理
        if isinstance(exc, PermissionDenied):
            response = VResponse(code=403, detail="没有访问权限", url=url)

        elif isinstance(exc, VException):
            response = VResponse(code=exc.code, detail=exc.msg, url=url)

        elif isinstance(exc, PermissException):
            response = PermissResponse(code=exc.code, detail=exc.msg, data=exc.data)
        else:
            # 出错的视图
            error = '服务器正忙,请稍后再试'
            response = VResponse(code=500, detail=error, url=url)
    else:
        response = VResponse(code=500, detail='异常错误', url=url)

    return response