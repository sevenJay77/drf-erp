from django.db import models


# 仓库
class Warehouse(models.Model):
    name = models.CharField(max_length=255, verbose_name="仓库名称")
    code = models.CharField(null=True, max_length=32, verbose_name="仓库编号")
    address = models.CharField(max_length=255, null=True, verbose_name="仓库地址")
    manager_id = models.IntegerField(null=True, verbose_name="负责人id")
    reserve = models.CharField(max_length=255, null=True)
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '仓库表'
        verbose_name_plural = verbose_name
        db_table = 'warehouse'


# 产品类型
class ProductCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name="类型名称")
    parent_id = models.IntegerField(null=True, verbose_name="父级id")
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '产品类型表'
        verbose_name_plural = verbose_name
        db_table = 'product_category'


# 产品信息
class Product(models.Model):
    code = models.CharField(null=True, max_length=32, verbose_name="产品编号")
    name = models.CharField(max_length=255, verbose_name="产品名称")
    spec = models.CharField(max_length=255, null=True, verbose_name="规格")
    category_id = models.IntegerField(null=True, verbose_name="分类id")
    delivery_place = models.CharField(max_length=255, null=True, verbose_name="提货地")
    steel_mill = models.CharField(max_length=64, null=True, verbose_name='钢厂')
    heat_number = models.CharField(max_length=64, null=True, verbose_name='炉号')
    unit = models.CharField(max_length=11, null=True, verbose_name='单位')
    img = models.TextField(null=True, verbose_name="图片")
    reserve = models.CharField(max_length=255, null=True)
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '产品信息表'
        verbose_name_plural = verbose_name
        db_table = 'product'

