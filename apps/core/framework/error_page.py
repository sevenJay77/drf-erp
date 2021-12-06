from rest_framework import status
from django.http import JsonResponse


'''
404抛出异常
'''
def page_not_found(request, **kwargs):
    return JsonResponse({"detail": "请求资源不存在"}, status=status.HTTP_404_NOT_FOUND)


'''
500抛出异常
'''
def server_error(request, **kwargs):
    return JsonResponse({"detail": "服务器错误，请稍后再试"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

