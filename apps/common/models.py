from django.db import models



# 资源上传表
class ResourceUpload(models.Model):
    file_url = models.CharField(max_length=255, verbose_name='文件路径')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    file_type = models.CharField(max_length=255, verbose_name='文件类型')
    storage = models.CharField(max_length=255, verbose_name='存储方式')
    create_user_id = models.IntegerField(null=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '资源上传'
        verbose_name_plural = verbose_name
        db_table = 'resource_upload'



# 扩展字段表
class CustomField(models.Model):
    table = models.CharField(max_length=100, verbose_name="扩展字段表名")
    name = models.CharField(max_length=100, verbose_name="字段")
    label = models.CharField(max_length=100, verbose_name="字段名")
    field_type = models.CharField(max_length=100, verbose_name="字段类型")
    custom_field_options = models.TextField(null=True, verbose_name="自定义属性")
    is_required = models.BooleanField(default=False, verbose_name="是否必填")
    is_default = models.BooleanField(default=False, verbose_name="系统默认")
    enable = models.BooleanField(default=False, verbose_name="是否启用")
    read_only = models.BooleanField(default=True, verbose_name="是否只读")
    is_show = models.BooleanField(default=True, verbose_name="是否展示")
    position = models.IntegerField(default=0, verbose_name="排序")
    is_order = models.BooleanField(default=False, verbose_name="是否排序")
    is_filter = models.BooleanField(default=False, verbose_name="是否筛选")
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '扩展字段表'
        verbose_name_plural = verbose_name
        db_table = 'custom_field'


