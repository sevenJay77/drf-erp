from django.db import models
from common.component import StandardModel

# 部门表
class Department(StandardModel):
    name = models.CharField(max_length=128, verbose_name="名称")
    parent_id = models.IntegerField(null=True, verbose_name="上级部门id")

    class Meta:
        verbose_name = "部门表"
        verbose_name_plural = verbose_name
        db_table = 'department'



# 权限组表
class PermissionGroup(models.Model):
    name = models.CharField(max_length=128, verbose_name="名称")
    parent_id = models.IntegerField(null=True, verbose_name="父级id")
    action = models.CharField(max_length=128, null=True, verbose_name="权限路由")
    type = models.SmallIntegerField(choices=((1, '操作权限'), (2, '数据权限'), (3, '字段权限')), default=1, verbose_name="权限类型")

    class Meta:
        verbose_name = "权限组表"
        verbose_name_plural = verbose_name
        db_table = 'permission_group'


# 角色
class Role(StandardModel):
    name = models.CharField(max_length=32, verbose_name="名称")
    permission = models.ManyToManyField(to=PermissionGroup)
    is_default = models.IntegerField(default=0, verbose_name="系统默认")

    class Meta:
        verbose_name = '角色表'
        verbose_name_plural = verbose_name
        db_table = 'role'


# 用户表
class User(StandardModel):
    gender_choice = ((0, '男'), (1, '女'))
    status_choice = ((0, '离职'), (1, '在职'))

    name = models.CharField(max_length=255, verbose_name="账号")
    password = models.CharField(max_length=255, verbose_name="密码")
    display_name = models.CharField(max_length=32, verbose_name='姓名')
    job_number = models.CharField(max_length=32, null=True, verbose_name='工号')
    mobile = models.CharField(max_length=32, null=True, verbose_name="手机号")
    private_mobile = models.CharField(max_length=32, null=True, verbose_name="私人手机号")
    email = models.CharField(max_length=255, null=True, verbose_name='邮箱')
    gender = models.SmallIntegerField(choices=gender_choice, null=True, verbose_name="性别")
    department_id = models.IntegerField(null=True, verbose_name="部门id")
    role_id = models.IntegerField(null=True, verbose_name="角色id")
    superior_id = models.SmallIntegerField(null=True, verbose_name="主管id")
    status = models.SmallIntegerField(choices=status_choice, default=1, verbose_name="状态")
    admit_guid = models.CharField(max_length=255, null=True, verbose_name="人脸系统guid")
    last_login = models.DateTimeField(null=True, verbose_name='最近登录时间')
    join_date = models.DateField(null=True, verbose_name="入职日期")
    quit_date = models.DateField(null=True, verbose_name="离职日期")

    class Meta:
        verbose_name = '用户表'
        verbose_name_plural = verbose_name
        db_table = 'users'



# 人事变动记录
class PersonnelRecord(models.Model):
    status_choice = ((0, '离职'), (1, '入职'))
    user_id = models.IntegerField(verbose_name="用户id")
    type = models.SmallIntegerField(choices=status_choice, default=1, verbose_name="类型")
    comment = models.CharField(max_length=255, null=True, verbose_name="备注")
    create_user_id = models.IntegerField(null=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = '人事变动记录'
        verbose_name_plural = verbose_name
        db_table = 'personnel_record'


# token表
class Token(models.Model):
    user_id = models.IntegerField(verbose_name="用户id")
    key = models.CharField(max_length=64, unique=True)
    source = models.CharField(max_length=64, null=True, verbose_name="来源")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = 'Token表'
        verbose_name_plural = verbose_name
        db_table = 'user_token'



# 验证码表
class VerifyCode(models.Model):
    event = models.CharField(max_length=255, verbose_name="场景类型")
    mobile = models.CharField(max_length=32, verbose_name="手机号")
    code = models.CharField(max_length=32, verbose_name="验证码")
    ip = models.CharField(max_length=32, verbose_name="ip地址")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '验证码表'
        verbose_name_plural = verbose_name
        db_table = 'verify_code'



# 门禁打卡记录
class AdmitRecord(models.Model):
    admit_name = models.CharField(max_length=11, verbose_name="员工名称")
    admit_guid = models.CharField(max_length=255, verbose_name="员工id")
    user_id = models.IntegerField(null=True)
    device_number = models.CharField(max_length=11, verbose_name="设备名称")
    device_no = models.CharField(max_length=20, verbose_name="设备编号")
    rec_mode = models.IntegerField(verbose_name="识别模式")
    file_path = models.TextField(null=True, verbose_name="现场图片")
    admit_type = models.IntegerField(choices=((0, '进门'), (1, '出门'), (2, '抓拍')), verbose_name="打卡类型")
    show_time = models.DateTimeField(verbose_name="识别时间")

    class Meta:
        verbose_name = '门禁考勤记录'
        verbose_name_plural = verbose_name
        db_table = 'admit_record'



# 考勤记录表
class AttendanceRecord(models.Model):
    code = models.CharField(max_length=11, verbose_name="编号")
    user_id = models.IntegerField()
    date = models.DateField(verbose_name="日期")
    first_admit = models.TimeField(null=True, max_length=0, verbose_name="签到时间")
    last_admit = models.TimeField(null=True, max_length=0, verbose_name="签退时间")
    out_duration = models.FloatField(default=None, null=True, verbose_name="外出时长")
    duty_duration = models.FloatField(default=0, null=True, verbose_name="上班时长")
    is_late = models.IntegerField(default=0, verbose_name="是否迟到")
    is_leave_early = models.IntegerField(default=0, verbose_name="是否早退")
    is_out_timeout = models.IntegerField(default=0, verbose_name="是否外出过长")
    time_interval_tuple = models.TextField(verbose_name="工作时间段")
    out_limit = models.FloatField(verbose_name="外出限制")
    is_revise = models.IntegerField(default=0, verbose_name="是否修正记录")
    comment = models.CharField(max_length=255, null=True, verbose_name="备注")
    created_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name="创建时间")
    update_user_id = models.IntegerField(null=True, verbose_name="修改人员")
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '考勤记录'
        verbose_name_plural = verbose_name
        db_table = 'attendance_record'



# 日历编辑记录
class CalendarEditRecord(models.Model):
    day = models.DateField(verbose_name="日期")
    is_holiday = models.IntegerField(verbose_name="是否放假")
    comment = models.CharField(max_length=255, null=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '日历编辑记录'
        verbose_name_plural = verbose_name
        db_table = 'calendar_edit_record'



# 考勤配置
class AttendanceConfig(models.Model):
    name = models.CharField(max_length=255, verbose_name="名称")
    value = models.TextField(null=True, verbose_name="配置")
    date = models.DateField(null=True, verbose_name="日期")
    create_user_id = models.IntegerField()
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '考勤配置'
        verbose_name_plural = verbose_name
        db_table = 'attendance_config'

