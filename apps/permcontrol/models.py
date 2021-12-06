from django.db import models


# 部门表
class Department(models.Model):
    name = models.CharField(max_length=128, verbose_name="名称")
    parent_id = models.IntegerField(null=True, verbose_name="上级部门id")
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

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
class Role(models.Model):
    name = models.CharField(max_length=32, verbose_name="名称")
    permission = models.ManyToManyField(to=PermissionGroup)
    is_default = models.IntegerField(default=0, verbose_name="系统默认")
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '角色表'
        verbose_name_plural = verbose_name
        db_table = 'role'


# 用户表
class User(models.Model):
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
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    create_user_id = models.IntegerField(null=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户表'
        verbose_name_plural = verbose_name
        db_table = 'users'



# 扩展字段表值
class UserCustomValue(models.Model):
    entity_id = models.IntegerField(verbose_name="记录id")
    field_name = models.CharField(max_length=255, verbose_name="字段name")
    value = models.CharField(max_length=255, null=True, verbose_name="值")
    version_no = models.CharField(max_length=11, null=True, verbose_name="版本号")
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)

    class Meta:
        verbose_name = '用户扩展值表'
        verbose_name_plural = verbose_name
        db_table = 'user_custom_value'



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

