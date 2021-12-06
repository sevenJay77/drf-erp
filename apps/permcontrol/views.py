import json
import time
import calendar

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Q

# swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from core.framework.v_exception import VException
from core.framework.hashers import make_password
from core.utils.functions import generate_token
from permcontrol.filter import PermissionFilter, RoleFilter, DepartmentFilter, UserFilter
from permcontrol.models import Token
from permcontrol.service import cache_user_expire_token, clean_user_expire_token, clean_cache_role_permission, \
    clean_user_related_data
from permcontrol.serializers import *

import logging

logger = logging.getLogger("django")


'''
账户基本操作
'''
class UserBasicView(viewsets.GenericViewSet):
    serializer_class = None

    filter_class = None

    pagination_class = None

    permission_classes = (AllowAny,)

    authentication_classes = ()

    @swagger_auto_schema(
        operation_description="登陆获取token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['account', 'password'],
            properties={
                'account': openapi.Schema(type=openapi.TYPE_STRING, description='用户名'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='密码'),
                'source': openapi.Schema(type=openapi.TYPE_INTEGER, description='登录平台(pc  mobile)'),
            },
        ),
        security=[],
        tags=['account'],
    )
    @transaction.atomic
    @action(methods=['post'], detail=False, url_path='login')
    def login_handler(self, request, *args, **kwargs):
        serializer = UserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        user = form_data['user']
        # 登录平台为 pc  mobile
        source = form_data.get('source', 'pc')
        if source not in ['pc', 'mobile']:
            raise VException(500, '请选择正确登录平台')
        '''
        pc，mobile 分别有token
        登录 刷新token
        '''
        time_now = datetime.datetime.now()
        # 获取token
        token = Token.objects.filter(user_id=user.id,
                                     source=source).first()
        if not token:
            # 创建token
            token = Token()
            token.user_id = user.id
            token.source = source
            token.key = generate_token()
        # 刷新token
        token.created_time = time_now
        token.save()
        # 最后登录时间
        user.last_login = time_now
        user.save()
        # 缓存token信息
        cache_user_expire_token(token.key, user.id, time_now)
        return Response({"detail": "登录成功", "data": token.key}, status=status.HTTP_200_OK)


'''
权限
'''
class PermissionView(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = PermissionSerializer

    pagination_class = None

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = PermissionFilter

    ordering = ('id')

    module_perms = ['role_permission']

    def get_queryset(self):
        return PermissionGroup.objects.all()

    @swagger_auto_schema(
        operation_description="权限列表",
        query_serializer=None,
        responses={200: openapi.Response('description', PermissionSerializer)},
        tags=['role_permission'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


'''
角色
'''
class RoleView(mixins.CreateModelMixin,
               mixins.RetrieveModelMixin,
               mixins.DestroyModelMixin,
               mixins.UpdateModelMixin,
               mixins.ListModelMixin,
               viewsets.GenericViewSet):
    serializer_class = RoleSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = RoleFilter

    pagination_class = None

    ordering = ('-created_time', '-id')

    module_perms = ['role_permission']

    def get_queryset(self):
        return Role.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '角色不存在')
        if not instance:
            raise VException(500, '角色不存在')
        return instance

    @swagger_auto_schema(
        operation_description="角色信息",
        query_serializer=None,
        responses={200: openapi.Response('description', RoleInfoSerializer)},
        tags=['permission'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RoleInfoSerializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="角色列表",
        query_serializer=None,
        responses={200: openapi.Response('description', RoleSerializer)},
        tags=['role_permission'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="创建角色",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
            },
        ),
        tags=['role_permission'],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        validate_ser = RoleCreateSerializer(data=request.data)
        validate_ser.is_valid(raise_exception=True)
        form_data = validate_ser.validated_data
        # 创建
        role = Role()
        role.name = form_data['name']
        role.create_user_id = request.user.id
        role.save()
        serializer = RoleInfoSerializer(role)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新角色",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'permission'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'permission': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.TYPE_INTEGER, description='权限列表'),
            },
        ),
        tags=['role_permission'],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = RoleSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        role = serializer.save(update_user_id=request.user.id)
        ser = RoleInfoSerializer(role)
        # 更新权限缓存
        user_list = User.objects.filter(role_id=instance.id,
                                        is_delete=0).all()
        id_list = []
        for user in user_list:
            id_list.append(user.id)
        clean_cache_role_permission(id_list)
        return Response({"detail": "更新成功", "data": ser.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新角色",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'permission': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.TYPE_INTEGER, description='权限列表'),
            },
        ),
        tags=['role_permission'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="删除角色",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['role_permission'],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default == 1:
            raise VException(500, '系统默认角色无法删除')
        # 判断角色下有无员工
        user = User.objects.filter(role_id=instance.id,
                                   is_delete=0).first()
        if user:
            raise VException(500, '该角色下还有员工，无法删除')
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)


'''
部门
'''
class DepartmentView(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):

    serializer_class = DepartmentSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = DepartmentFilter

    pagination_class = None

    ordering = ('-created_time', '-id')

    module_perms = ['department_user']

    def get_queryset(self):
        return Department.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '部门不存在')
        if not instance:
            raise VException(500, '部门不存在')
        return instance

    @swagger_auto_schema(
        operation_description="部门信息",
        query_serializer=None,
        responses={200: openapi.Response('description', DepartmentSerializer)},
        tags=['department_user'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="部门列表",
        query_serializer=None,
        responses={200: openapi.Response('description', DepartmentSerializer)},
        tags=['department_user'],
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
        except Exception as e:
            raise VException(500, '没有数据')
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="创建部门",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='上级部门id'),
            },
        ),
        tags=['department_user'],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(create_user_id=request.user.id)
        return Response({"detail": "创建成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新部门",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='上级部门id'),
            },
        ),
        tags=['department_user'],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = DepartmentSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(update_user_id=request.user.id)
        return Response({"detail": "更新成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新部门",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='名称'),
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='上级部门id'),
            },
        ),
        tags=['department_user'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="删除部门",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['department_user'],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 判断角色下有无员工
        user = User.objects.filter(department_id=instance.id,
                                   is_delete=0).first()
        if user:
            raise VException(500, '该部门下还有员工，无法删除')
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "删除成功"}, status=status.HTTP_200_OK)


'''
个人信息
'''
class PersonalInfoView(viewsets.GenericViewSet):
    serializer_class = None

    pagination_class = None

    filter_class = None

    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="获取个人用户信息",
        query_serializer=None,
        responses={200: openapi.Response('description', PersonInfoSerializer)},
        tags=['account'],
    )
    @transaction.atomic
    @action(methods=['get'], detail=False, url_path='info')
    def person_detail(self, request, *args, **kwargs):
        user = request.user
        serializer = PersonInfoSerializer(user)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="修改密码",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='当前密码'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='新密码'),
            },
        ),
        tags=['account'],
    )
    @transaction.atomic
    @action(methods=['put'], detail=False, url_path='change_password')
    def change_password_handler(self, request, *args, **kwargs):
        serializer = ChangeUserPasswdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 密码校验
        form_data = serializer.validated_data
        user = request.user
        new_password = form_data['new_password']
        old_password = form_data['old_password']
        # 密码校验
        pwd_valid = check_password(old_password, user.password)
        if not pwd_valid:
            raise VException(500, "原密码错误")
        user.password = make_password(new_password)
        user.save()
        # 删除之前的token（pc, mobile）
        token_list = Token.objects.filter(user_id=user.id).all()
        for token in token_list:
            clean_user_expire_token(token.key)
            token.delete()
        return Response({"detail": "修改密码成功"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="退出登录",
        query_serializer=None,
        tags=['account'],
    )
    @action(methods=['delete'], detail=False, url_path='logout')
    def logout_handler(self, request, *args, **kwargs):
        user = request.user
        request_token = request.META.get('HTTP_ACCESS_TOKEN')
        # 删除token记录
        token = Token.objects.filter(user_id=user.id,
                                     key=request_token).first()
        if token:
            clean_user_expire_token(token.key)
            token.delete()
        return Response({"detail": "注销成功"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="修改个人资料",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['gender', 'mobile'],
            properties={
                'gender': openapi.Schema(type=openapi.TYPE_NUMBER, description='性别'),
                'mobile': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'private_mobile': openapi.Schema(type=openapi.TYPE_STRING, description='私人手机号'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱'),
            },
        ),
        tags=['account'],
    )
    @action(methods=['put'], detail=False, url_path='edit')
    def person_edit(self, request, *args, **kwargs):
        user = request.user
        serializer = PersonEditSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "修改成功", "data": serializer.data}, status=status.HTTP_200_OK)


'''
用户
'''
class UserView(mixins.CreateModelMixin,
               mixins.RetrieveModelMixin,
               mixins.DestroyModelMixin,
               mixins.UpdateModelMixin,
               mixins.ListModelMixin,
               viewsets.GenericViewSet):

    serializer_class = UserSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filter_class = UserFilter

    ordering_fields = ['created_time']

    ordering = ('-created_time', '-id')

    module_perms = ['department_user']

    edit_perms = ['reset_password', 'quit', 'sync_database']

    def get_queryset(self):
        return User.objects.filter(is_delete=0).all()

    def get_object(self):
        try:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            queryset = self.get_queryset()
            instance = queryset.filter(**filter_kwargs).first()
        except:
            raise VException(500, '用户不存在')
        if not instance:
            raise VException(500, '用户不存在')
        return instance

    @swagger_auto_schema(
        operation_description="用户信息",
        query_serializer=None,
        responses={200: openapi.Response('description', UserSerializer)},
        tags=['department_user'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="用户列表",
        query_serializer=None,
        responses={200: openapi.Response('description', UserSerializer)},
        tags=['department_user'],
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
        operation_description="创建用户",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'job_number', 'display_name', 'gender', 'mobile', 'department_id', 'role_id'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='账号'),
                'job_number': openapi.Schema(type=openapi.TYPE_STRING, description='工号'),
                'display_name': openapi.Schema(type=openapi.TYPE_STRING, description='姓名'),
                'gender': openapi.Schema(type=openapi.TYPE_NUMBER, description='性别'),
                'mobile': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'private_mobile': openapi.Schema(type=openapi.TYPE_STRING, description='私人手机号'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱'),
                'department_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='部门id'),
                'superior_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='主管id'),
                'role_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='角色id'),
                'join_date': openapi.Schema(type=openapi.TYPE_STRING, description='入职时间'),
            },
        ),
        tags=['department_user'],
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(create_user_id=request.user.id,
                               password=make_password('111111'))
        user.admit_guid = None
        user.save()
        # 添加人事信息
        record = PersonnelRecord()
        record.user_id = user.id
        record.type = 1
        record.create_user_id = request.user.id
        record.save()
        return Response({"detail": "创建成功, 默认密码：111111", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新用户",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'job_number', 'display_name', 'gender', 'mobile', 'department_id', 'role_id'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='登录账号'),
                'job_number': openapi.Schema(type=openapi.TYPE_STRING, description='工号'),
                'display_name': openapi.Schema(type=openapi.TYPE_STRING, description='姓名'),
                'gender': openapi.Schema(type=openapi.TYPE_NUMBER, description='性别'),
                'mobile': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'private_mobile': openapi.Schema(type=openapi.TYPE_STRING, description='私人手机号'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱'),
                'department_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='部门id'),
                'superior_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='主管id'),
                'role_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='角色id'),
                'join_date': openapi.Schema(type=openapi.TYPE_STRING, description='入职时间'),
                'quit_date': openapi.Schema(type=openapi.TYPE_STRING, description='离职时间'),
                'admit_guid': openapi.Schema(type=openapi.TYPE_STRING, description='门禁guid'),
            },
        ),
        tags=['department_user'],
    )
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = UserSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(update_user_id=request.user.id)
        # 清除权限缓存
        clean_cache_role_permission([instance.id])
        return Response({"detail": "更新成功", "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="更新用户",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='登录账号'),
                'job_number': openapi.Schema(type=openapi.TYPE_STRING, description='工号'),
                'display_name': openapi.Schema(type=openapi.TYPE_STRING, description='姓名'),
                'gender': openapi.Schema(type=openapi.TYPE_NUMBER, description='性别'),
                'mobile': openapi.Schema(type=openapi.TYPE_STRING, description='手机号'),
                'private_mobile': openapi.Schema(type=openapi.TYPE_STRING, description='私人手机号'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱'),
                'department_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='部门id'),
                'superior_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='主管id'),
                'role_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='角色id'),
                'join_date': openapi.Schema(type=openapi.TYPE_STRING, description='入职时间'),
                'quit_date': openapi.Schema(type=openapi.TYPE_STRING, description='离职时间'),
                'admit_guid': openapi.Schema(type=openapi.TYPE_STRING, description='门禁guid'),
            },
        ),
        tags=['department_user'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="重置密码",
        query_serializer=None,
        responses={200: openapi.Response('重置密码成功')},
        tags=['department_user'],
    )
    @action(methods=['put'], detail=True, url_path='reset_password')
    @transaction.atomic
    def reset_password(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.password = make_password('111111')
        instance.update_user_id = request.user.id
        instance.save()
        # 删除token记录
        token_list = Token.objects.filter(user_id=instance.id).all()
        for token in token_list:
            clean_user_expire_token(token.key)
            token.delete()
        return Response({"detail": "重置成功，密码为：111111"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="离职用户",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quit_date'],
            properties={
                'quit_date': openapi.Schema(type=openapi.TYPE_STRING, description='离职时间'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='离职原因'),
            },
        ),
        tags=['department_user'],
    )
    @action(methods=['put'], detail=True, url_path='quit')
    @transaction.atomic
    def quit(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == 0:
            raise VException(500, '员工已离职')
        serializer = UserQuitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_date = serializer.validated_data
        # 更新人员信息
        instance.update_user_id = request.user.id
        instance.status = 0
        instance.quit_date = form_date['quit_date']
        instance.save()
        # 添加人事信息
        record = PersonnelRecord()
        record.user_id = instance.id
        record.type = 0
        record.create_user_id = request.user.id
        if 'comment' in form_date:
            record.comment = form_date['comment']
        record.save()
        # 删除token记录
        token_list = Token.objects.filter(user_id=instance.id).all()
        for token in token_list:
            clean_user_expire_token(token.key)
            token.delete()
        # 清除关联数据
        clean_user_related_data(instance.id)
        # 清除权限缓存
        clean_cache_role_permission([instance.id])
        return Response({"detail": "离职成功, 账户已失效"}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="彻底删除用户",
        query_serializer=None,
        responses={200: openapi.Response('删除成功')},
        tags=['department_user'],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 1:
            raise VException(500, '请先离职该员工')
        # 删除
        instance.is_delete = 1
        instance.update_user_id = request.user.id
        instance.save()
        return Response({"detail": "彻底删除用户成功"}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="同步系统字段",
        query_serializer=None,
        responses={200: openapi.Response('描述')},
        tags=['custom_field'],
    )
    @action(methods=['post'], detail=False, url_path='sync_database')
    def sync_database(self, request, *args, **kwargs):
        # 排序字段
        order_dict = self.ordering_fields
        # filter 字段
        filter_dict = self.filter_class.Meta.fields
        serializer = UserSerializer()
        data = serializer.to_custom_field()
        # 同步系统字段
        for field in data:
            queryset = CustomField.objects.filter(table='user',
                                                  is_delete=0,
                                                  name=field['name'])
            # 排序、筛选标志
            field['table'] = 'user'
            if field['name'] in order_dict:
                field['is_order'] = 1
            else:
                field['is_order'] = 0
            if field['name'] in filter_dict:
                field['is_filter'] = 1
            else:
                field['is_filter'] = 0

            if not queryset.exists():
                CustomField.objects.create(**field)
                continue
            # 更新数据
            queryset.update(**field)

        return Response({"detail": "同步成功"}, status=status.HTTP_200_OK)




# 用户自定义字段
class UserCustomFieldView(viewsets.GenericViewSet):

    serializer_class = None

    pagination_class = None

    filter_class = None

    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="获取用户自定义字段",
        query_serializer=None,
        responses={200: openapi.Response('描述')},
        tags=['custom_field'],
    )
    def list(self, request, *args, **kwargs):
        custom_fields = CustomField.objects.filter(is_delete=0,
                                                   table='user').order_by('position', 'id').all()
        serializer = CustomFieldSerializer(custom_fields, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


