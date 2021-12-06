from collections import OrderedDict
# Non-field imports, but public API
from rest_framework.fields import SkipField
# NOQA # isort:skip
from rest_framework.relations import PKOnlyObject
from django.db import transaction

from rest_framework import serializers
from core.framework.v_exception import VException
from core.utils.functions import filter_space
from warehouse.models import Warehouse, ProductCategory, Product
from permcontrol.models import User

# 仓库
class WarehouseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少仓库名称", "blank": "仓库名称不能为空", "null": "仓库名称不能为空"}, trim_whitespace=False)
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    manager_id = serializers.IntegerField(required=False, allow_null=True, error_messages={"invalid": "选择正确的负责人"})
    reserve = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    code = serializers.CharField(read_only=True)
    manager = serializers.SerializerMethodField(read_only=True)
    create_user_id = serializers.IntegerField(read_only=True)
    update_user_id = serializers.IntegerField(read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Warehouse
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
        info = {}
        if obj.manager_id:
            manager = User.objects.filter(id=obj.manager_id,
                                          is_delete=0).first()
            if manager:
                info = {
                    'id': manager.id,
                    'display_name': manager.display_name,
                    'mobile': manager.mobile
                }
        return info



# 产品类型
class ProductCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少类型名称", "blank": "类型名称不能为空", "null": "类型名称不能为空"}, trim_whitespace=False)
    parent_id = serializers.IntegerField(required=False, allow_null=True, error_messages={"invalid": "选择正确父级"})

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent_id']

    def validate_parent_id(self, attrs):
        if attrs:
            parent_category = ProductCategory.objects.filter(id=attrs,
                                                             is_delete=0).first()
            if not parent_category:
                raise VException(500, '父级类型不存在')
            if self.instance is not None:
                if attrs == self.instance.id:
                    raise VException(500, '不能选择自己作为父级类型')
                if attrs == self.instance.parent_id:
                    raise VException(500, '父级类型选择失败')
        return attrs



# 产品
class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={"required": "缺少产品名称", "blank": "产品名称不能为空", "null": "产品名称不能为空"}, trim_whitespace=False)
    spec = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True, error_messages={"invalid": "选择正确产品类型"})
    delivery_place = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    steel_mill = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    heat_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    unit = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    img = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reserve = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category = serializers.SerializerMethodField(read_only=True)
    code = serializers.CharField(read_only=True)
    create_user_id = serializers.IntegerField(read_only=True)
    update_user_id = serializers.IntegerField(read_only=True)
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Product
        exclude = ['is_delete']

    def validate_category_id(self, attrs):
        if attrs:
            category = ProductCategory.objects.filter(id=attrs,
                                                      is_delete=0).first()
            if not category:
                raise VException(500, '所选产品类型不存在')
        return attrs

    def get_category(self, obj):
        info = {}
        if obj.category_id:
            category = ProductCategory.objects.filter(id=obj.category_id).first()
            if category:
                ser = ProductCategorySerializer(category)
                info = ser.data
        return info

