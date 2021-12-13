import json
import datetime
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from rest_framework.permissions import AllowAny

# swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from core.utils.functions import generate_random_key
from common.serializers import  *
from common.models import ResourceUpload
from core.ali_service.ali_oss import AliOssClientInstance


import logging

logger = logging.getLogger("django")


'''
资源上传
'''
class ResourceUploadView(viewsets.GenericViewSet):

    serializer_class = ResourceUploadSerializer

    pagination_class = None

    filter_class = None

    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="资源上传oss",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['file'],
            properties={
                'file': openapi.Schema(type=openapi.TYPE_FILE, description='文件'),
                'file_type': openapi.Schema(type=openapi.TYPE_STRING, description='文件类型数组'),
                'usage': openapi.Schema(type=openapi.TYPE_STRING, description='分类标签'),
            },
        ),
        tags=['common'],
    )
    @action(methods=['post'], detail=False, url_path='upload')
    def upload_handler(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        file = form_data['file']
        file_type_list = form_data['file_type']
        usage = form_data.get('usage', 'common')

        ali_oss_client = AliOssClientInstance.get_storage_instance()
        oss_url, file_type = ali_oss_client.upload_multi_file(file, file_type_list, usage)
        # 入库
        resource = ResourceUpload()
        resource.file_name = file.name
        resource.file_url = oss_url
        resource.file_type = file_type
        resource.storage = 'AliOss'
        resource.create_user_id = request.user.id
        resource.save()
        return Response({"detail": "上传成功", "data": oss_url}, status=status.HTTP_200_OK)


'''
自定义字段
'''
class CustomFieldView(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = CustomFieldSerializer

    pagination_class = None

    filter_class = None

    module_perms = ['custom_field']

    edit_perms = ['update_position']

    def get_queryset(self):
        return CustomField.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '自定义字段不存在')
        if not instance:
            raise VException(500, '自定义字段不存在')
        return instance


    @swagger_auto_schema(
        operation_description="自定义字段信息",
        query_serializer=None,
        responses={200: openapi.Response('description', CustomFieldSerializer)},
        tags=['custom_field'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="创建自定义字段",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['label', 'field_type', 'table', 'is_required', 'enable', 'is_show', 'is_order', 'is_filter'],
            properties={
                'table': openapi.Schema(type=openapi.TYPE_STRING, description='扩展字段表名'),
                'label': openapi.Schema(type=openapi.TYPE_STRING, description='字段名称'),
                'field_type': openapi.Schema(type=openapi.TYPE_STRING, description="字段类型"),
                'custom_field_options': openapi.Schema(type=openapi.TYPE_STRING, description="属性"),
                'is_required': openapi.Schema(type=openapi.TYPE_NUMBER, description="是否必填"),
                'enable':  openapi.Schema(type=openapi.TYPE_NUMBER, description="是否启用"),
                'is_show': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否展示"),
                'is_order': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否排序"),
                'is_filter': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否筛选"),

            },
        ),
        tags=['custom_field'],
    )
    def create(self, request, *args, **kwargs):
        serializer = CustomFieldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        field_name = "{}_{}".format(form_data.get("field_type"), generate_random_key(5))
        serializer.save(create_user_id=request.user.id,
                        name=field_name)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新自定义字段",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['label', 'field_type', 'is_required', 'enable', 'is_show', 'is_order', 'is_filter'],
            properties={
                'label': openapi.Schema(type=openapi.TYPE_STRING, description='字段名称'),
                'field_type': openapi.Schema(type=openapi.TYPE_STRING, description="字段类型"),
                'custom_field_options': openapi.Schema(type=openapi.TYPE_STRING, description="属性"),
                'is_required': openapi.Schema(type=openapi.TYPE_NUMBER, description="是否必填"),
                'enable': openapi.Schema(type=openapi.TYPE_NUMBER, description="是否启用"),
                'is_show': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否展示"),
                'is_order': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否排序"),
                'is_filter': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否筛选"),
            },
        ),
        tags=['custom_field'],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = CustomFieldUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        # 更新自定义字段
        # 如果是系统自定义字段，只能修改 is_show  label
        if instance.is_default == 1:
            if 'is_show' in form_data.keys():
                instance.is_show = form_data['is_show']
            if  'label' in form_data.keys():
                instance.label = form_data['label']
            instance.update_user_id = request.user.id
            instance.save()
        else:
            # 保存
            for attr, value in form_data.items():
                setattr(instance, attr, value)
            instance.update_user_id = request.user.id
            instance.save()

        ser = CustomFieldSerializer(instance)
        return Response({"detail": "更新成功", "data": ser.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新自定义字段",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'label': openapi.Schema(type=openapi.TYPE_STRING, description='字段名称'),
                'field_type': openapi.Schema(type=openapi.TYPE_STRING, description="字段类型"),
                'custom_field_options': openapi.Schema(type=openapi.TYPE_STRING, description="属性"),
                'is_required': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否必填"),
                'enable':  openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否启用"),
                'is_show': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否展示"),
                'is_order': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否排序"),
                'is_filter': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="是否筛选"),
            },
        ),
        tags=['custom_field'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="删除自定义字段",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['custom_field'],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default == 1:
            raise VException(500, '业务字段，不能删除')
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新排序位置",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['custom_field'],
            properties={
                'custom_field': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.TYPE_NUMBER, description='自定义字段'),
            },
        ),
        tags=['custom_field'],
    )
    @action(methods=['put'], detail=False, url_path='update_position')
    def update_position(self, request, *args, **kwargs):
        custom_field = request.data.get('custom_field', [])
        if not custom_field:
            raise VException(500, '请输入排序字段')
        for index in range(len(custom_field)):
            id = custom_field[index]
            record = CustomField.objects.filter(id=id,
                                                is_delete=0).first()
            if not record:
                continue
            record.position = index
            record.update_user_id = request.user.id
            record.save()
        return Response({"detail": "更新成功"}, status=status.HTTP_200_OK)



# 自定义字段列表
class CustomFieldListView(viewsets.GenericViewSet):

    serializer_class = None

    pagination_class = None

    filter_class = None

    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="获取自定义字段",
        query_serializer=None,
        responses={200: openapi.Response('描述')},
        tags=['custom_field'],
    )
    @action(methods=['get'], detail=False, url_path='(?P<table>\w+)')
    def get_list(self, request, table, *args, **kwargs):
        custom_fields = CustomField.objects.filter(is_delete=0,
                                                   table=table).order_by('position', 'id').all()
        serializer = CustomFieldSerializer(custom_fields, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)





