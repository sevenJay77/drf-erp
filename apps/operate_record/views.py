import json
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
# swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from core.framework.v_exception import VException
from core.utils.functions import JsonToDatetime, format_multi_conditions
from operate_record.service import notify_ws
from operate_record.serializers import *
from operate_record.filter import NotifyFilter
from permcontrol.models import User
import logging

logger = logging.getLogger("django")


'''
后管发送消息列表
'''
class AdminUserNotifyView(mixins.ListModelMixin,
                          viewsets.GenericViewSet):

    serializer_class = AdminNotifyRecordSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    ordering = ('-created_time', '-id')

    module_perms = ['admin_notify']

    def get_queryset(self):
        queryset = AdminOperateRecord.objects.filter(module="NotifyMessage").all()
        return queryset

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '通知消息不存在')
        if not instance:
            raise VException(500, '通知消息不存在')
        return instance

    @swagger_auto_schema(
        operation_description="查看通知列表",
        query_serializer=None,
        responses={200: openapi.Response('description', AdminNotifyRecordSerializer)},
        security=[],
        tags=['notify'],
    )
    # 列表数据
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(page, many=True)
        # 判断已读
        return self.get_paginated_response(serializer.data)


    @swagger_auto_schema(
        operation_description="创建消息通知",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'module', 'record_sign'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='标题'),
                'module': openapi.Schema(type=openapi.TYPE_STRING, description='模块'),
                'record_sign': openapi.Schema(type=openapi.TYPE_STRING, description='主键'),
                'user_list': openapi.Schema(type=openapi.TYPE_STRING, description='用户id列表'),

            },
        ),
        tags=['notify'],
    )
    def create(self, request, *args, **kwargs):
        serializer = AdminNotifySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        user_id_list = form_data.get('user_list', None)
        # 创建记录
        admin_operate = AdminOperateRecord()
        admin_operate.module = "NotifyMessage"
        admin_operate.operate_type = 0
        admin_operate.new_data = json.dumps(form_data, cls=JsonToDatetime)
        admin_operate.comment = "后管消息通知"
        admin_operate.user_id = request.user.id
        admin_operate.save()

        if user_id_list is None:
            # 发送给所有人
            user_list = User.objects.filter(is_delete=0).all()
        else:
            user_id_list = format_multi_conditions(user_id_list)
            user_list = User.objects.filter(is_delete=0,
                                            id__in=user_id_list).all()

        for admin_user in user_list:
            message = {
                'user_id': admin_user.id,
                'title': form_data['title'],
                'module': form_data['module'],
                'record_sign': form_data['record_sign']
            }
            notify_ws(message)
        ser = AdminNotifyRecordSerializer(admin_operate)
        return Response({"detail": "创建成功", "data": ser.data}, status=status.HTTP_200_OK)


'''
用户消息列表
'''
class UserNotifyView(mixins.ListModelMixin,
                     viewsets.GenericViewSet):

    serializer_class = NotifyMessageSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = NotifyFilter

    ordering = ('-created_time', '-id')

    module_perms = ['notify']

    def get_queryset(self):
        user = self.request.user
        if not user:
            return NotifyMessage.objects.none()
        queryset = NotifyMessage.objects.filter(user_id=user.id).all()
        return queryset

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '通知消息不存在')
        if not instance:
            raise VException(500, '通知消息不存在')
        return instance

    @swagger_auto_schema(
        operation_description="查看个人通知列表",
        query_serializer=None,
        responses={200: openapi.Response('description', NotifyMessageSerializer)},
        security=[],
        tags=['notify'],
    )
    # 列表数据
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(page, many=True)
        # 未读消息
        data =  self.paginator.get_paginated_data(serializer.data)
        unread_count = queryset.filter(is_read=0).count()
        data['unread_count'] = unread_count
        return Response({'data': data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="标记通知信息已读",
        query_serializer=None,
        responses={200: openapi.Response('description', NotifyMessageSerializer)},
        tags=['notify'],
    )
    @action(methods=['put'], detail=False, url_path='(?P<pk>\w+)/read')
    def read_handler(self, request, *args, **kwargs):
        instance = self.get_object()
        # 更新已阅
        if instance.is_read == 0:
            instance.is_read = 1
            instance.save()
        serializer = self.get_serializer(instance)
        return Response({'detail': "操作成功", 'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="标记所有通知信息已读",
        query_serializer=None,
        responses={200: openapi.Response('操作成功')},
        tags=['notify'],
    )
    @action(methods=['put'], detail=False, url_path='read_all')
    def read_all_handler(self, request, *args, **kwargs):
        user = request.user
        queryset = NotifyMessage.objects.filter(user_id=user.id).all()
        for instance in queryset:
            instance.is_read = 1
            instance.save()

        return Response({'detail': "操作成功"}, status=status.HTTP_200_OK)



