from django.db import models
from common.component import StandardModel


# 仓库
class Warehouse(StandardModel):
    name = models.CharField(max_length=255, verbose_name="仓库名称")
    code = models.CharField(null=True, max_length=32, verbose_name="仓库编号")
    address = models.CharField(max_length=255, null=True, verbose_name="仓库地址")
    manager_id = models.IntegerField(null=True, verbose_name="负责人id")

    class Meta:
        verbose_name = '仓库表'
        verbose_name_plural = verbose_name
        db_table = 'warehouse'


# 产品信息
class Product(StandardModel):
    code = models.CharField(null=True, max_length=32, verbose_name="产品编号")
    name = models.CharField(max_length=255, verbose_name="产品名称")

    class Meta:
        verbose_name = '产品信息表'
        verbose_name_plural = verbose_name
        db_table = 'product'

