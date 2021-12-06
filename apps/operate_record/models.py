from django.db import models

# 操作记录
class AdminOperateRecord(models.Model):
    OPERATE_LIST = (
        (0, '添加'),
        (1, '编辑'),
        (2, '删除'),
    )

    operate_type = models.SmallIntegerField(choices=OPERATE_LIST, default=0, verbose_name='类型')
    module = models.CharField(max_length=255, verbose_name="模块")
    record_sign = models.CharField(max_length=255, verbose_name="记录标记", null=True)
    new_data = models.TextField(verbose_name="数据", null=True)
    comment = models.CharField(max_length=255, null=True, verbose_name="操作备注")
    user_id = models.IntegerField(null=True, verbose_name="操作用户")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = '操作记录'
        verbose_name_plural = verbose_name
        db_table = 'operate_admin_record'


# 消息通知表
class NotifyMessage(models.Model):
    title = models.CharField(max_length=255)
    is_read = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    module = models.CharField(max_length=255, verbose_name="模块", null=True)
    record_sign = models.CharField(max_length=255, verbose_name="记录标记", null=True)
    tenant_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)
    create_user_id = models.IntegerField(null=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间', null=True)

    class Meta:
        verbose_name = '消息通知表'
        verbose_name_plural = verbose_name
        db_table = 'user_notify_message'