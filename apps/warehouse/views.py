import json
import datetime
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from rest_framework.permissions import AllowAny
from core.framework.ordering_filter import CustomStandardOrdering

# swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from warehouse.filter import WarehouseFilter, ProductFilter
from warehouse.serializers import *
from common.models import CustomField
from warehouse.service import generate_warehouse_code
import logging

logger = logging.getLogger("django")



'''
仓库
'''
class WarehouseView(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = WarehouseSerializer

    filter_backends = [CustomStandardOrdering]

    # 系统排序字段
    order_dict = ['created_time', 'id']
    # 系统排序筛选字段
    filter_dict = ['code']
    # 默认排序字段
    ordering = ('-created_time', '-id')

    module_perms = ['warehouse']

    edit_perms = ['sync_database']

    def get_queryset(self):
        return Warehouse.objects.filter(is_delete=0).order_by().all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '仓库不存在')
        if not instance:
            raise VException(500, '仓库不存在')
        return instance


    @swagger_auto_schema(
        operation_description="仓库信息",
        query_serializer=None,
        responses={200: openapi.Response('description', WarehouseSerializer)},
        tags=['warehouse'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="仓库列表",
        query_serializer=None,
        responses={200: openapi.Response('description', WarehouseSerializer)},
        tags=['warehouse'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
        except Exception as e:
            logger.error(e)
            raise VException(500, '没有数据')
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="创建仓库",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='地址'),
                'manager_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='管理员id'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
            },
        ),
        tags=['warehouse'],
    )
    def create(self, request, *args, **kwargs):
        serializer = WarehouseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 编号
        code = generate_warehouse_code('CK')
        serializer.save(create_user_id=request.user.id,
                        code=code)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新仓库",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='地址'),
                'manager_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='管理员id'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
            },
        ),
        tags=['warehouse'],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = WarehouseSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(update_user_id=request.user.id)
        return Response({"detail": "更新成功", "data": serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新仓库",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='地址'),
                'manager_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='管理员id'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
            },
        ),
        tags=['warehouse'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="删除仓库",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['warehouse'],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="同步系统字段",
        query_serializer=None,
        responses={200: openapi.Response('描述')},
        tags=['custom_field'],
    )
    @action(methods=['post'], detail=False, url_path='sync_database')
    def sync_database(self, request, *args, **kwargs):
        serializer = WarehouseSerializer()
        table = serializer.Meta.table
        data = serializer.to_custom_field()
        with transaction.atomic():
            # 同步系统字段
            for field in data:
                queryset = CustomField.objects.filter(table=table,
                                                      is_delete=0,
                                                      name=field['name'])
                # 排序、筛选标志
                field['table'] = table
                if field['name'] in self.order_dict:
                    field['is_order'] = 1
                else:
                    field['is_order'] = 0
                if field['name'] in self.filter_dict:
                    field['is_filter'] = 1
                else:
                    field['is_filter'] = 0

                if not queryset.exists():
                    CustomField.objects.create(**field)
                    if field['name'] == "created_time":
                        raise VException(500, '')
                    continue
                # 更新数据
                queryset.update(**field)
        return Response({"detail": "同步成功"}, status=status.HTTP_200_OK)


'''
产品
'''
class ProductView(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):

    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = ProductFilter

    ordering = ('-created_time', '-id')

    module_perms = ['product']

    def get_queryset(self):
        return Product.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '产品不存在')
        if not instance:
            raise VException(500, '产品不存在')
        return instance

    @swagger_auto_schema(
        operation_description="产品信息",
        query_serializer=None,
        responses={200: openapi.Response('description', ProductSerializer)},
        tags=['product'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="产品列表",
        query_serializer=None,
        responses={200: openapi.Response('description', ProductSerializer)},
        tags=['product'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="创建产品",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='产品名称'),
            },
        ),
        tags=['product'],
    )
    def create(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = generate_warehouse_code('CP')
        serializer.save(create_user_id=request.user.id,
                        code=code)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新产品",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='产品名称'),
            },
        ),
        tags=['product'],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = ProductSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(update_user_id=request.user.id)
        return Response({"detail": "更新成功", "data": serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新产品",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='产品名称'),
            },
        ),
        tags=['product'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="删除产品",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['product'],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)

