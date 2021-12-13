from rest_framework import serializers
from core.framework.v_exception import VException
from core.utils.functions import filter_space
from warehouse.models import Warehouse, Product
from permcontrol.models import User
from common.component import StandardSerializer

import logging

logger = logging.getLogger("django")


# 仓库
class WarehouseSerializer(StandardSerializer):
    id = serializers.IntegerField(read_only=True, help_text='id')
    code = serializers.CharField(read_only=True, help_text="仓库编号")
    name = serializers.CharField(required=True, error_messages={"required": "缺少仓库名称", "blank": "仓库名称不能为空", "null": "仓库名称不能为空"}, trim_whitespace=False, help_text="仓库名称")
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="仓库地址")
    manager_id = serializers.IntegerField(required=False, allow_null=True, error_messages={"invalid": "选择正确的负责人"}, help_text="负责人id")
    manager = serializers.SerializerMethodField(read_only=True, help_text="负责人")

    class Meta:
        model = Warehouse
        table = 'warehouse'
        exclude = ['is_delete']

    def validate_name(self, attrs):
        name = filter_space(attrs, True)
        queryset = Warehouse.objects.filter(is_delete=0,
                                            name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.id)
        if queryset.exists():
            raise VException(500, '仓库名称已存在')
        return name

    def validate_manager_id(self, attrs):
        if attrs:
            manger = User.objects.filter(id=attrs,
                                         is_delete=0).first()
            if not manger:
                raise VException(500, '所选负责人不存在')

        return attrs

    def get_manager(self, obj):
        name = ""
        if obj.manager_id:
            manager = User.objects.filter(id=obj.manager_id,
                                          is_delete=0).first()
            if manager:
                name = manager.display_name
        return name



# 产品
class ProductSerializer(StandardSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True, error_messages={"required": "缺少产品名称", "blank": "产品名称不能为空", "null": "产品名称不能为空"}, trim_whitespace=False)

    class Meta:
        model = Product
        table = 'product'
        exclude = ['is_delete']
