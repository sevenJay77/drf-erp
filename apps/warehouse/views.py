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

from warehouse.filter import WarehouseFilter, ProductCategoryFilter, ProductFilter
from warehouse.serializers import *
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

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = WarehouseFilter

    ordering = ('-created_time', '-id')

    module_perms = ['warehouse']

    def get_queryset(self):
        return Warehouse.objects.filter(is_delete=0).all()

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
    @transaction.atomic
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
    @transaction.atomic
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
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)





'''
产品类型
'''
class ProductCategoryView(mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):

    serializer_class = ProductCategorySerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = ProductCategoryFilter

    pagination_class = None

    ordering = ('-created_time', '-id')

    module_perms = ['product']

    def get_queryset(self):
        return ProductCategory.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '产品类型不存在')
        if not instance:
            raise VException(500, '产品类型不存在')
        return instance


    @swagger_auto_schema(
        operation_description="产品类型信息",
        query_serializer=None,
        responses={200: openapi.Response('description', ProductCategorySerializer)},
        tags=['product'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="产品类型列表",
        query_serializer=None,
        responses={200: openapi.Response('description', ProductCategorySerializer)},
        tags=['product'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="创建产品类型",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='父级id'),
            },
        ),
        tags=['product'],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = ProductCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(create_user_id=request.user.id)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新产品类型",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='父级id'),
            },
        ),
        tags=['product'],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = ProductCategorySerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(update_user_id=request.user.id)
        return Response({"detail": "更新成功", "data": serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="更新产品类型",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='上级部门id'),
            },
        ),
        tags=['product'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="删除产品类型",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['product'],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)


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
                'spec': openapi.Schema(type=openapi.TYPE_STRING, description='规格'),
                'category_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='产品类型'),
                'delivery_place': openapi.Schema(type=openapi.TYPE_STRING, description='提货地'),
                'steel_mill': openapi.Schema(type=openapi.TYPE_STRING, description='钢厂'),
                'heat_number': openapi.Schema(type=openapi.TYPE_STRING, description='炉号'),
                'unit': openapi.Schema(type=openapi.TYPE_STRING, description='计量单位'),
                'img': openapi.Schema(type=openapi.TYPE_STRING, description='图片'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
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
                'spec': openapi.Schema(type=openapi.TYPE_STRING, description='规格'),
                'category_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='产品类型'),
                'delivery_place': openapi.Schema(type=openapi.TYPE_STRING, description='提货地'),
                'steel_mill': openapi.Schema(type=openapi.TYPE_STRING, description='钢厂'),
                'heat_number': openapi.Schema(type=openapi.TYPE_STRING, description='炉号'),
                'unit': openapi.Schema(type=openapi.TYPE_STRING, description='计量单位'),
                'img': openapi.Schema(type=openapi.TYPE_STRING, description='图片'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
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
                'spec': openapi.Schema(type=openapi.TYPE_STRING, description='规格'),
                'category_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='产品类型'),
                'delivery_place': openapi.Schema(type=openapi.TYPE_STRING, description='提货地'),
                'steel_mill': openapi.Schema(type=openapi.TYPE_STRING, description='钢厂'),
                'heat_number': openapi.Schema(type=openapi.TYPE_STRING, description='炉号'),
                'unit': openapi.Schema(type=openapi.TYPE_STRING, description='计量单位'),
                'img': openapi.Schema(type=openapi.TYPE_STRING, description='图片'),
                'reserve': openapi.Schema(type=openapi.TYPE_STRING, description='备注'),
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

