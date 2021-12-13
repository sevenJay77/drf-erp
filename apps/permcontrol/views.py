import json
import time
import calendar

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Q

# swagger
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from config.config import WOModuleConfig
from core.framework.v_exception import VException
from core.framework.hashers import make_password
from core.utils.functions import generate_token
from permcontrol.filter import PermissionFilter, RoleFilter, DepartmentFilter
from permcontrol.models import Token, AdmitRecord
from permcontrol.service import cache_user_expire_token, clean_user_expire_token, clean_cache_role_permission, \
    clean_user_related_data, summary_database_function, generate_revise_database, get_attendance_calendar,edit_attendance_config, get_attendance_config
from core.framework.ordering_filter import CustomStandardOrdering, StandardOrdering
from permcontrol.serializers import *
from common.models import CustomField

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

    filter_backends = [DjangoFilterBackend, StandardOrdering]

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

    filter_backends = [DjangoFilterBackend, StandardOrdering]

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

    filter_backends = [DjangoFilterBackend, StandardOrdering]

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
        with transaction.atomic():
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

    filter_backends = [CustomStandardOrdering]
    # 系统排序字段
    order_dict = ['created_time']
    # 系统排序筛选字段
    filter_dict = ['status', 'mobile', 'display_name']

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
    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save(create_user_id=request.user.id,
                                   password=make_password('111111'))
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
    def reset_password(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
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
    def quit(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == 0:
            raise VException(500, '员工已离职')
        serializer = UserQuitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_date = serializer.validated_data
        with transaction.atomic():
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
        serializer = UserSerializer()
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
                    continue
                # 更新数据
                queryset.update(**field)

        return Response({"detail": "同步成功"}, status=status.HTTP_200_OK)




'''
WO平台对接
'''
class WOServiceView(viewsets.GenericViewSet):
    serializer_class = None

    pagination_class = None

    filter_class = None

    permission_classes = (AllowAny,)

    authentication_classes = ()

    @swagger_auto_schema(
        operation_description="打卡信息回调",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={},
        ),
        tags=['common'],
    )
    @action(methods=['post'], detail=False, url_path='face_event')
    def face_event(self, request, *args, **kwargs):
        logger.info("门禁回调数据：{}".format(request.data))
        # 判断回调数据
        event_msg = request.data.get('eventMsg', "")
        if event_msg:
            try:
                # 解码
                msg_dict = json.loads(event_msg)
                result = int(msg_dict['result'])
                # 识别为注册用户
                if result == 1:
                    user_id = None
                    user = User.objects.filter(admit_guid=msg_dict['admitGuid'],
                                               is_delete=0).first()
                    if user:
                        user_id = user.id
                    admit_record = AdmitRecord()
                    admit_record.admit_name = msg_dict['admitName']
                    admit_record.user_id = user_id
                    admit_record.admit_guid = msg_dict['admitGuid']
                    admit_record.device_name = msg_dict['deviceName']
                    admit_record.device_no = msg_dict['deviceNo']
                    if msg_dict['deviceNo'] in WOModuleConfig.in_device_no:
                        admit_record.admit_type = 0
                    elif msg_dict['deviceNo'] in WOModuleConfig.out_device_no:
                        admit_record.admit_type = 1
                    else:
                        admit_record.admit_type = 2
                    # 1:人像识别, 2:刷卡识别 ,3:人卡合一 4,人证比对 7:密码识别 8 二维码识别
                    admit_record.rec_mode = int(msg_dict['recMode'])
                    admit_record.file_path = msg_dict.get('filePath', '')
                    show_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(msg_dict['showTime'] / 1000)))
                    show_datetime = datetime.datetime.strptime(show_time, "%Y-%m-%d %H:%M:%S")
                    admit_record.show_time = show_datetime
                    admit_record.save()
            except Exception as e:
                logger.error('门禁回调数据异常, error {}'.format(e))

        return Response({"detail": "回调成功"}, status=status.HTTP_200_OK)


'''
考勤信息
'''
class AttendanceView(viewsets.GenericViewSet):

    serializer_class = UpdateAttendanceSerializer

    pagination_class = None

    filter_class = None

    module_perms = ['attendance']

    edit_perms = ['edit_record', 'edit_calendar', 'edit_config']

    retrieve_perms = ['summary_attendance', 'get_calendar', 'month_summary', 'get_config']

    @swagger_auto_schema(
        operation_description="查看考勤统计",
        manual_parameters=[
            openapi.Parameter(name='date', in_=openapi.IN_QUERY, description="日期(Y-m-d)", type=openapi.TYPE_STRING),
            openapi.Parameter(name='user_id', in_=openapi.IN_QUERY, description="用户id", type=openapi.TYPE_NUMBER)],
        responses={200: openapi.Response('description')},
        tags=['attendance'],
    )
    @action(methods=['get'], detail=False, url_path='summary')
    def summary_attendance(self, request, *args, **kwargs):
        # 查看统计
        today_date = request.GET.get('date', None)
        user_id = request.GET.get('user_id', None)
        size = request.GET.get('size', 10)
        page = request.GET.get('page', 1)

        # 没有日期参数，则显示当天
        if today_date is None:
            time_now = datetime.datetime.now()
            today_date = time_now.strftime('%Y-%m-%d')
        # 转为datetime
        try:
            today_date = datetime.datetime.strptime(today_date, "%Y-%m-%d")
        except:
            raise VException(500, '日期格式错误')

        # 考勤配置
        attendance_config = get_attendance_config(today_date)
        time_interval_tuple = attendance_config['time_interval_tuple']
        out_limit = attendance_config['out_limit']
        exclude_user = attendance_config['exclude_user']

        admit_summary = []
        # 没有人员参数，则显示所有人
        if user_id is None:
            # 查找未离职的人员考勤记录
            user_queryset = User.objects.filter(Q(quit_date__isnull=True) | Q(quit_date__gt=today_date),
                                                ~Q(id__in=exclude_user),
                                                Q(status=1)).all()
            for user in user_queryset:
                info = summary_database_function(user, today_date, time_interval_tuple, out_limit)
                admit_summary.append(info)
        else:
            user = User.objects.filter(id=user_id).first()
            if not user:
                raise VException(500, '员工不存在')
            info = summary_database_function(user, today_date, time_interval_tuple, out_limit)
            admit_summary.append(info)
        # 列表分页
        per_page_count = int(size)
        current_page = int(page)
        start = (current_page - 1) * per_page_count
        end = current_page * per_page_count
        data = {
            'count': len(admit_summary),
            'results': admit_summary[start:end]
        }
        return Response({"data": data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="编辑考勤记录",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'date'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_NUMBER, description='员工id'),
                'date': openapi.Schema(type=openapi.TYPE_STRING, description='日期'),
                'first_admit': openapi.Schema(type=openapi.TYPE_STRING, description='签到时间'),
                'last_admit': openapi.Schema(type=openapi.TYPE_STRING, description='签退时间'),
                'out_duration': openapi.Schema(type=openapi.TYPE_NUMBER, description='外出时长'),
                'comment': openapi.Schema(type=openapi.TYPE_NUMBER, description='备注'),
            },
        ),
        tags=['attendance'],
    )
    @action(methods=['put'], detail=False, url_path='edit_record')
    def edit_record(self, request, *args, **kwargs):
        # 校验索引数据
        serializer = UpdateAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        user_id = form_data['user_id']
        date = form_data['date']
        code = "{}{}".format(date.strftime('%Y%m%d'), user_id)
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise VException(500, '员工不存在')

        # 不允许修改大于等于今天日期的
        time_now = datetime.datetime.now()
        today_now_datetime = datetime.datetime(time_now.year, time_now.month, time_now.day)
        if date >= today_now_datetime:
            raise VException(500, '当前日期不支持编辑')
        # 有无修正数据
        origin_record = AttendanceRecord.objects.filter(code=code,
                                                        is_revise=0).first()
        if not origin_record:
            raise VException(500, '尚未有统计数据')

        # 重新计算
        revise_record = AttendanceRecord.objects.filter(code=code,
                                                        is_revise=1).first()
        if not revise_record:
            # 复制原打卡记录
            revise_record = AttendanceRecord()
            revise_record.code = code
            revise_record.user_id = user_id
            revise_record.date = date
            revise_record.out_duration = None
            revise_record.duty_duration = origin_record.duty_duration
            revise_record.is_late = origin_record.is_late
            revise_record.is_leave_early = origin_record.is_leave_early
            revise_record.is_out_timeout = origin_record.is_out_timeout
            revise_record.time_interval_tuple = origin_record.time_interval_tuple
            revise_record.out_limit = origin_record.out_limit
            revise_record.is_revise = 1
            revise_record.save()

        ser = EditAttendanceSerializer(instance=revise_record, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        form_data = ser.validated_data
        ser.save()
        # 重新生成判断数据
        generate_revise_database(origin_record, revise_record, form_data)
        return Response({"detail": "更新成功"}, status=status.HTTP_200_OK)



    @swagger_auto_schema(
        operation_description="编辑考勤日历",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['day', 'is_holiday'],
            properties={
                'day': openapi.Schema(type=openapi.TYPE_STRING, description='日期 2021-11-24'),
                'is_holiday': openapi.Schema(type=openapi.TYPE_NUMBER, description='是否休假'),
            },
        ),
        tags=['attendance'],
    )
    @action(methods=['put'], detail=False, url_path='edit_calendar')
    def edit_calendar(self, request, *args, **kwargs):
        serializer = UpdateCalendarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        day = form_data['day']
        is_holiday = form_data['is_holiday']
        comment = form_data.get('comment', None)
        record = CalendarEditRecord.objects.filter(day=day).first()
        if not record:
            record = CalendarEditRecord()
            record.day = day
            record.create_user_id = request.user.id
        else:
            record.update_user_id = request.user.id
        if not comment is None:
            record.comment = comment
        record.is_holiday = is_holiday
        record.save()

        data = {
            'day': day.strftime("%Y-%m-%d"),
            'is_holiday': is_holiday,
            'comment': record.comment
        }

        return Response({"detail": "编辑成功", "data": data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="查看考勤日历",
        manual_parameters=[
            openapi.Parameter(name='date', in_=openapi.IN_QUERY, description="日期(%Y-%m)", type=openapi.TYPE_STRING)],
        responses={200: openapi.Response('description')},
        tags=['attendance'],
    )
    @action(methods=['get'], detail=False, url_path='calendar')
    def get_calendar(self, request, *args, **kwargs):
        # 查看统计
        today_date = request.GET.get('date', None)
        if today_date is None:
            today_datetime = datetime.datetime.now()
        else:
            try:
                today_datetime = datetime.datetime.strptime(today_date, "%Y-%m")
            except:
                raise VException(500, '输入的日期格式错误')
        data = get_attendance_calendar(today_datetime)
        return Response({"data": data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="月度统计结果",
        manual_parameters=[
            openapi.Parameter(name='date', in_=openapi.IN_QUERY, description="日期(%Y-%m)", type=openapi.TYPE_STRING)],
        responses={200: openapi.Response('description')},
        tags=['attendance'],
    )
    @action(methods=['get'], detail=False, url_path='month_summary')
    def month_summary(self, request, *args, **kwargs):
        # 查看统计
        today_date = request.GET.get('date', None)
        size = request.GET.get('size', 10)
        page = request.GET.get('page', 1)

        time_now = datetime.datetime.now()
        if today_date is None:
            today_date = time_now.strftime("%Y-%m")
        try:
            today_datetime = datetime.datetime.strptime(today_date, "%Y-%m")
        except:
            raise VException(500, '输入的日期格式错误')
        # 计算考勤天数
        calendar_data = get_attendance_calendar(today_datetime)
        # 考勤配置
        attendance_config = get_attendance_config(today_datetime)
        time_interval_tuple = attendance_config['time_interval_tuple']
        out_limit = attendance_config['out_limit']
        exclude_user = attendance_config['exclude_user']
        # 获取考勤人员
        attendance_data = []
        user_queryset = User.objects.filter(Q(quit_date__isnull=True) | Q(quit_date__gt=today_datetime),
                                            ~Q(id__in=exclude_user),
                                            Q(status=1)).all()
        for user in user_queryset:
            duty_days = 0
            user_attendance_info = {
                'user_id': user.id,
                'name': user.display_name,
                'job_number': user.job_number,
                'date': today_datetime.strftime('%Y-%m'),
                # 应打卡天数
                'attendance_days': duty_days,
                # 出勤天数
                'duty_days': 0,
                # 出勤时长
                'duty_duration_hours': 0,
                # 外出时长
                'out_duration_hours': 0,
                # 异常天数
                'abnormal_days': 0,
                'late_days': 0,
                'leave_early_days': 0,
                'out_timeout_days': 0,
            }

            # 考勤统计
            for calendar_info in calendar_data:
                calendar_day = datetime.datetime.strptime(calendar_info['day'], "%Y-%m-%d")
                # 今日和假期不纳入统计
                today_now_datetime = datetime.datetime(time_now.year, time_now.month, time_now.day)
                if calendar_day >= today_now_datetime or calendar_info['is_holiday'] == 1:
                    continue
                duty_days += 1
                info = summary_database_function(user, calendar_day,time_interval_tuple, out_limit)
                result_out_duration = info['result_out_duration']
                result_duty_duration = info['result_duty_duration']
                is_late = info['is_late']
                is_leave_early = info['is_leave_early']
                is_out_timeout = info['is_out_timeout']
                if result_duty_duration > 0:
                    user_attendance_info['duty_days'] += 1
                if is_late == 1:
                    user_attendance_info['late_days'] += 1
                if is_leave_early == 1:
                    user_attendance_info['leave_early_days'] += 1
                if is_out_timeout == 1:
                    user_attendance_info['out_timeout_days'] += 1
                if is_late == 1 or is_leave_early == 1 or is_out_timeout == 1:
                    user_attendance_info['abnormal_days'] += 1

                user_attendance_info['duty_duration_hours'] += result_duty_duration
                user_attendance_info['out_duration_hours'] += result_out_duration

            user_attendance_info['duty_duration_hours'] = round(user_attendance_info['duty_duration_hours'], 2)
            user_attendance_info['out_duration_hours'] = round(user_attendance_info['out_duration_hours'], 2)
            user_attendance_info['attendance_days'] = duty_days
            attendance_data.append(user_attendance_info)

        # 列表分页
        per_page_count = int(size)
        current_page = int(page)
        start = (current_page - 1) * per_page_count
        end = current_page * per_page_count
        data = {
            'count': len(attendance_data),
            'results': attendance_data[start:end]
        }

        return Response({"data": data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="编辑考勤配置",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['time_interval_tuple', 'out_limit', 'exclude_user'],
            properties={
                'time_interval_tuple': openapi.Schema(type=openapi.TYPE_STRING, description='考勤时段'),
                'out_limit': openapi.Schema(type=openapi.TYPE_NUMBER, description='超时阈值'),
                'exclude_user': openapi.Schema(type=openapi.TYPE_STRING, description='不考勤人员'),
            },
        ),
        tags=['attendance'],
    )
    @action(methods=['put'], detail=False, url_path='edit_config')
    def edit_config(self, request, *args, **kwargs):
        serializer = AttendanceConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form_data = serializer.validated_data
        edit_attendance_config(form_data, request.user)
        return Response({"detail": "编辑成功, 配置隔天生效", "data":form_data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="获取考勤配置",
        tags=['attendance'],
    )
    @action(methods=['get'], detail=False, url_path='get_config')
    def get_config(self, request, *args, **kwargs):
        info = {
            'time_interval_tuple': '',
            'out_limit': 0,
            'exclude_user': ''
        }
        queryset = AttendanceConfig.objects.filter(name='time_interval_tuple').order_by('-id').first()
        if queryset:
            info['time_interval_tuple'] = queryset.value
        queryset = AttendanceConfig.objects.filter(name='out_limit').order_by('-id').first()
        if queryset:
            info['out_limit'] = queryset.value
        queryset = AttendanceConfig.objects.filter(name='exclude_user').order_by('-id').first()
        if queryset:
            info['exclude_user'] = queryset.value
        return Response({"data":info}, status=status.HTTP_200_OK)