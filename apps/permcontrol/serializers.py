import datetime
import json
import six
from collections import OrderedDict

from rest_framework import serializers
from core.utils.functions import filter_space
from core.framework.hashers import check_password
from core.utils.functions import match_mobile, match_email
from core.framework.v_exception import VException
from permcontrol.models import User, PermissionGroup, Role, Department, AttendanceConfig, CalendarEditRecord, AttendanceRecord, PersonnelRecord
from permcontrol.service import get_full_tree_permission
from common.component import StandardSerializer


import logging

logger = logging.getLogger("django")

# Token
class UserTokenSerializer(serializers.Serializer):
    account = serializers.CharField(required=True, error_messages={"required": "缺少登录账号", "blank": "登录账号不能为空", "null": "登录账号不能为空"}, trim_whitespace=False)
    password = serializers.CharField(required=True, trim_whitespace=False, error_messages={"required": "缺少密码", "blank": "密码不能为空", "null": "密码不能为空"}, style={'input_type': 'password'})
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        account = attrs['account']
        password = attrs['password']
        # 验证登录
        user = User.objects.filter(name=account,
                                   is_delete=0).first()
        if user is None:
            raise serializers.ValidationError("账号未注册", code='authorization')
        if user.status == 0:
            raise serializers.ValidationError("该账号已被注销", code='authorization')
        # 密码校验
        pwd_valid = check_password(password, user.password)
        if not pwd_valid:
            raise serializers.ValidationError("密码不正确", code='authorization')
        attrs['user'] = user
        return attrs



# 权限
class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PermissionGroup
        fields = '__all__'


# 创建角色
class RoleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少角色名", "blank": "角色名不能为空", "null": "角色名不能为空"}, trim_whitespace=False)

    def validate_name(self, attrs):
        name = filter_space(attrs, True)
        queryset = Role.objects.filter(is_delete=0,
                                       name=name).first()
        if queryset:
            raise VException(500, '角色名已存在')
        return name



# 角色
class RoleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少角色名", "blank": "角色名不能为空", "null": "角色名不能为空"}, trim_whitespace=False)
    permission = serializers.ListField(required=True, write_only=True, allow_empty=True, allow_null=True, error_messages={"required": "缺少权限数组", "not_a_list": "权限数组错误"})
    is_default = serializers.IntegerField(read_only=True)
    is_delete = serializers.IntegerField(read_only=True)
    create_user_id = serializers.IntegerField(read_only=True)
    update_user_id = serializers.IntegerField(read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Role
        fields = '__all__'

    # 重复校验
    def validate_name(self, attrs):
        name = filter_space(attrs, True)
        queryset = Role.objects.filter(is_delete=0,
                                       name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.id)
        if queryset.exists():
            raise VException(500, '角色名已存在')
        return name


    def validate_permission(self, attrs):
        permission_list = []
        for permission_id in attrs:
            if not permission_id:
                continue
            if permission_id in permission_list:
                continue
            child_list = get_full_tree_permission(permission_id)
            if child_list:
                permission_list += child_list
        # 去重
        permission_list = list(set(permission_list))
        return permission_list



class RoleInfoSerializer(serializers.ModelSerializer):

    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Role
        fields = '__all__'



# 部门
class DepartmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少部门名称", "blank": "部门名称不能为空", "null": "部门名称不能为空"}, trim_whitespace=False)
    parent_id = serializers.IntegerField(required=False, allow_null=True, error_messages={"invalid": "选择正确上级部门"})

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent_id']

    def validate_parent_id(self, attrs):
        if attrs:
            parent_department = Department.objects.filter(id=attrs,
                                                          is_delete=0).first()
            if not parent_department:
                raise VException(500, '上级部门不存在')
            if self.instance is not None:
                if attrs == self.instance.id:
                    raise VException(500, '不能选择自己作为上级部门')
                if attrs == self.instance.parent_id:
                    raise VException(500, '上级部门选择失败')
        return attrs



# 简略个人信息
class UserSimpleSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField(read_only=True)
    join_date = serializers.DateField(format="%Y-%m-%d", read_only=True)

    class Meta:
        model = User
        exclude = ['id', 'job_number', 'display_name', 'mobile', 'private_mobile', 'email', 'department', 'join_date']

    def get_department(self, obj):
        info = {}
        if obj.department_id:
            department = Department.objects.filter(id=obj.department_id,
                                                   is_delete=0).first()
            if department:
                ser = DepartmentSerializer(department)
                info = ser.data
        return info


# 个人信息
class PersonInfoSerializer(serializers.ModelSerializer):
    superior = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)
    permission_list = serializers.SerializerMethodField(read_only=True)
    department = serializers.SerializerMethodField(read_only=True)
    join_date = serializers.DateField(format="%Y-%m-%d", read_only=True)
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = User
        exclude = ['password', 'is_delete']

    def get_superior(self, obj):
        info = {}
        if obj.superior_id:
            superior = User.objects.filter(id=obj.superior_id,
                                           is_delete=0).first()
            if superior:
                ser = UserSimpleSerializer(superior)
                info = ser.data
        return info

    def get_role(self, obj):
       return obj.role

    def get_permission_list(self, obj):
        return obj.permission

    def get_department(self, obj):
        info = {}
        if obj.department_id:
            department = Department.objects.filter(id=obj.department_id,
                                                   is_delete=0).first()
            if department:
                ser = DepartmentSerializer(department)
                info = ser.data
        return info


class ChangeUserPasswdSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, min_length=6,  error_messages={"required": "缺少当前密码", "min_length": "当前密码长度过短", "blank": "当前密码不能为空", "null": "当前密码不能为空"}, trim_whitespace=False)
    new_password = serializers.CharField(required=True, min_length=6, error_messages={"required": "缺少新密码", "min_length": "新密码长度过短", "blank": "新密码不能为空", "null": "新密码不能为空"}, trim_whitespace=False)



class PersonEditSerializer(serializers.ModelSerializer):
    gender = serializers.ChoiceField(required=True, choices=User.gender_choice,  error_messages={"required": "请选择性别", "invalid_choice": "请选择正确性别", "null": "性别不能为空"})
    mobile = serializers.CharField(required=True, error_messages={"required": "缺少手机号", "blank": "手机号不能为空", "null": "手机号不能为空"})
    private_mobile = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['gender', 'mobile', 'private_mobile', 'email']

    def validate_mobile(self, attrs):
        if not match_mobile(attrs):
            raise VException(500, "手机号格式错误")
        return attrs

    def validate_private_mobile(self, attrs):
        if attrs:
            if not match_mobile(attrs):
                raise VException(500, "私人手机号格式错误")
        return attrs

    def validate_email(self, attrs):
        if attrs:
            if not match_email(attrs):
                raise VException(500, "邮箱格式错误")
        return attrs



class UserSerializer(StandardSerializer):
    id = serializers.IntegerField(read_only=True, help_text='id')
    name = serializers.CharField(required=True, min_length=2, error_messages={"required": "缺少账号", "blank": "账号不能为空", "null": "账号不能为空", "min_length": "账号需大于2位"}, help_text='账号')
    job_number = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='工号')
    display_name = serializers.CharField(required=True, error_messages={"required": "缺少姓名", "blank": "姓名不能为空", "null": "姓名不能为空"}, help_text='姓名')
    gender = serializers.ChoiceField(required=True, choices=User.gender_choice, error_messages={"required": "请选择性别", "invalid_choice": "请选择正确性别", "null": "性别不能为空"}, help_text='性别')
    mobile = serializers.CharField(required=True, error_messages={"required": "缺少手机号", "blank": "手机号不能为空", "null": "手机号不能为空"}, help_text='手机号')
    private_mobile = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='私人手机号')
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='邮箱')
    department_id = serializers.IntegerField(required=True, allow_null=True, error_messages={"required": "缺少部门", "invalid": "选择正确部门"}, help_text='部门id')
    superior_id = serializers.IntegerField(required=True, allow_null=True, error_messages={"required": "缺少主管", "invalid": "选择正确主管"}, help_text='主管id')
    role_id = serializers.IntegerField(required=True, allow_null=True, error_messages={"required": "缺少角色", "invalid": "选择正确角色"}, help_text='角色id')
    join_date = serializers.DateField(required=False, allow_null=True, input_formats=["%Y-%m-%d"], error_messages={"invalid": "入职日期格式错误", "date": "入职日期格式错误", "make_aware": "入职日期格式错误", "overflow": "入职日期格式错误"}, format="%Y-%m-%d", help_text='入职日期')
    quit_date = serializers.DateField(required=False, allow_null=True, input_formats=["%Y-%m-%d"], error_messages={"invalid": "离职日期格式错误", "date": "离职日期格式错误", "make_aware": "离职日期格式错误", "overflow": "离职日期格式错误"}, format="%Y-%m-%d", help_text='离职日期')
    admit_guid = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='门禁guid')
    status = serializers.ChoiceField(choices=User.status_choice, read_only=True, help_text='状态')
    superior = serializers.SerializerMethodField(read_only=True, help_text='主管')
    role = serializers.SerializerMethodField(read_only=True, help_text='角色')
    department = serializers.SerializerMethodField(read_only=True, help_text='部门')
    create_user_id = serializers.IntegerField(read_only=True, help_text='创建用户id')
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text='上次登录时间')
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text='创建时间')
    update_user_id = serializers.IntegerField(read_only=True, help_text='更新用户id')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text='更新时间')

    class Meta:
        model = User
        table = 'user'
        exclude = ['password', 'is_delete']


    def validate_name(self, attrs):
        name = filter_space(attrs, True)
        queryset = User.objects.filter(is_delete=0,
                                       name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.id)
        if queryset.exists():
            raise VException(500, '登录账号已存在')
        return name

    def validate_mobile(self, attrs):
        if attrs:
            if not match_mobile(attrs):
                raise VException(500, "手机号格式错误")
        return attrs

    def validate_private_mobile(self, attrs):
        if attrs:
            if not match_mobile(attrs):
                raise VException(500, "私人手机号格式错误")
        return attrs

    def validate_email(self, attrs):
        if attrs:
            if not match_email(attrs):
                raise VException(500, "邮箱格式错误")
        return attrs

    def validate_job_number(self, attrs):
        if attrs:
            queryset = User.objects.filter(is_delete=0,
                                           job_number=attrs)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.id)
            if queryset.exists():
                raise VException(500, '工号已被占用')
        return attrs

    def validate_department_id(self, attrs):
        if attrs:
            department = Department.objects.filter(id=attrs,
                                                   is_delete=0).first()
            if not department:
                raise VException(500, '所选部门不存在')
        return attrs

    def validate_superior_id(self, attrs):
        if attrs:
            superior = User.objects.filter(id=attrs,
                                           is_delete=0).first()
            if not superior:
                raise VException(500, '所选主管不存在')
            if self.instance is not None:
                if attrs == self.instance.id:
                    raise VException(500, '不能选择自己作为主管')
        return attrs

    def validate_role_id(self, attrs):
        if attrs:
            role = Role.objects.filter(id=attrs,
                                       is_delete=0).first()
            if not role:
                raise VException(500, '所选角色不存在')
        return attrs

    def get_superior(self, obj):
        display_name = ""
        if obj.superior_id:
            superior = User.objects.filter(id=obj.superior_id,
                                           is_delete=0).first()
            if superior:
                display_name = superior.display_name
        return display_name

    def get_role(self, obj):
        name = ""
        if obj.role_id:
            role = Role.objects.filter(id=obj.role_id,
                                       is_delete=0).first()
            if role:
                name = role.name
        return name

    def get_department(self, obj):
        name = ""
        if obj.department_id:
            department = Department.objects.filter(id=obj.department_id,
                                                   is_delete=0).first()
            if department:
                name = department.name
        return name




class UserQuitSerializer(serializers.Serializer):
    quit_date = serializers.DateTimeField(required=True, input_formats=["%Y-%m-%d"], error_messages={"required": "请输入离职日期", "null": "离职日期不能为空", "invalid": "离职日期格式错误", "date": "离职日期格式错误", "make_aware": "离职日期格式错误", "overflow": "离职日期格式错误"}, format="%Y-%m-%d")
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)



class UpdateAttendanceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, error_messages={"required": "请填写用户id", "invalid": "请输入正确的用户id", "null": "用户id不能为空"})
    date = serializers.DateTimeField(required=True, input_formats=["%Y-%m-%d"], error_messages={"required": "请输入日期", "null": "日期不能为空", "invalid": "日期格式错误", "date": "日期格式错误", "make_aware": "日期格式错误", "overflow": "日期格式错误"}, format="%Y-%m-%d")



class EditAttendanceSerializer(serializers.ModelSerializer):
    first_admit = serializers.TimeField(required=False, allow_null=True, input_formats=["%H:%M:%S"], error_messages={"required": "请输入签到时间", "invalid": "签到时间格式错误"}, format="%H:%M:%S")
    last_admit = serializers.TimeField(required=False, allow_null=True, input_formats=["%H:%M:%S"], error_messages={"required": "请输入签退时间", "invalid": "签退时间格式错误"}, format="%H:%M:%S")
    out_duration = serializers.FloatField(required=False, allow_null=True, error_messages={"required": "缺少外出时长", "invalid": "外出时长格式错误"})
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = AttendanceRecord
        fields = ['first_admit', 'last_admit', 'out_duration', 'comment']



class UpdateCalendarSerializer(serializers.Serializer):
    day = serializers.DateField(required=True, input_formats=["%Y-%m-%d"], error_messages={"required": "请输入日期", "null": "日期不能为空", "invalid": "日期格式错误", "date": "日期格式错误", "make_aware": "日期格式错误", "overflow": "日期格式错误"}, format="%Y-%m-%d")
    is_holiday = serializers.ChoiceField(required=True, allow_null=True, choices=((0, '否'), (1, '是')), error_messages={"required": "请选择是否放假", "invalid_choice": "请选择正确是否放假"})
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)



class AttendanceConfigSerializer(serializers.Serializer):
    time_interval_tuple = serializers.CharField(required=True, error_messages={"required": "请填写考勤时段", "blank": "考勤时段不能为空", "null": "考勤时段不能为空"})
    out_limit = serializers.FloatField(required=True, error_messages={"required": "缺少外出阈值", "invalid": "外出阈值格式错误"})
    exclude_user = serializers.CharField(required=True, allow_null=True, allow_blank=True, error_messages={"required": "缺少不考勤人员设置"})

    def validate_time_interval_tuple(self, attrs):
        try:
            time_interval = json.loads(attrs)
        except Exception as e:
            raise VException(500, "考勤时段错误")
        if len(time_interval) != 2:
            raise VException(500, "请配置2个考勤时段")
        for interval in time_interval:
            if len(interval) != 2:
                raise VException(500, "请配置正确时段")
            try:
                first_admit = interval[0]
                last_admit = interval[1]
                first_admit_datetime = datetime.datetime.strptime(first_admit, "%H:%M")
                last_admit_datetime = datetime.datetime.strptime(last_admit, "%H:%M")
            except:
                raise VException(500, '请填写[%H:%M]格式日期')

            if first_admit_datetime >= last_admit_datetime:
                raise VException(500, '起始时间需小于结束时间')

        if time_interval[0][1] > time_interval[1][0]:
            raise VException(500, '第2个时区必须大于第1个时区')

        return time_interval


    def validate_exclude_user(self, attrs):
        if attrs:
            try:
                exclude_user = attrs.split(',')
                for user_id in exclude_user:
                    user = User.objects.filter(is_delete=0,
                                               status=1,
                                               id=user_id).first()
                    if not user:
                        raise VException(500, '人员不存在')
            except Exception as e:
                raise VException(500, '考勤参数错误')
        return attrs
