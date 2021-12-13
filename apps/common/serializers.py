from rest_framework import serializers
from core.framework.v_exception import VException
from core.utils.functions import format_multi_conditions
from common.models import CustomField
from common.component import custom_type_list
import json


class ResourceUploadSerializer(serializers.Serializer):

    file = serializers.FileField(required=True, error_messages={"empty": "文件内容为空", "required": "缺少文件", "invalid": "请正确上传文件", "blank": "文件不能为空", "no_name": "文件名不能为空"})
    file_type = serializers.CharField(default="image", trim_whitespace=False, error_messages={"blank": "文件类型不能为空", "null": "文件类型不能为空"})
    usage = serializers.CharField(required=False, allow_blank=True, allow_null=True)


    def validate_file_type(self, attrs):
        type_list = format_multi_conditions(attrs)
        for file_type in type_list:
            if file_type not in ['image', 'apk', 'video', 'wgt', 'document']:
                raise VException(500, '文件类型不支持')
        return type_list



class CustomFieldSerializer(serializers.ModelSerializer):
    table = serializers.CharField(required=True, error_messages={"required": "缺少表名", "blank": "表名不能为空", "null": "表名不能为空"})
    label = serializers.CharField(required=True, error_messages={"required": "缺少字段名称", "blank": "字段名称不能为空", "null": "字段名称不能为空"})
    field_type = serializers.CharField(required=True, error_messages={"required": "缺少字段类型", "blank": "字段类型不能为空", "null": "字段类型不能为空"})
    custom_field_options = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_required = serializers.BooleanField(required=True, error_messages={"required": "缺少是否必填", "invalid": "选择是否必填", "null": "是否必填不能为空"})
    enable = serializers.BooleanField(required=True, error_messages={"required": "缺少是否启用", "invalid": "选择是否启用", "null": "是否启用不能为空"})
    is_show = serializers.BooleanField(required=True, error_messages={"required": "缺少是否展示", "invalid": "选择是否展示", "null": "是否展示不能为空"})
    is_order = serializers.BooleanField(required=True, error_messages={"required": "缺少是否排序", "invalid": "选择是否排序", "null": "是否排序不能为空"})
    is_filter = serializers.BooleanField(required=True, error_messages={"required": "缺少是否筛选", "invalid": "选择是否筛选", "null": "是否筛选不能为空"})
    name = serializers.CharField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    position = serializers.IntegerField(read_only=True)
    create_user_id = serializers.IntegerField(read_only=True)
    update_user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomField
        exclude = ['is_delete', 'created_time', 'updated_time']

    def validate(self, attrs):
        field_type = attrs['field_type']
        if field_type not in custom_type_list:
            raise VException(500, '字段类型不存在')

        custom_field_options = attrs.get('custom_field_options')
        if field_type == 'ChoiceField' and not custom_field_options:
            raise VException(500, '缺少选项配置')

        return attrs

    def validate_custom_field_options(self, attrs):
        if attrs:
            try:
                json.loads(attrs)
            except Exception as e:
                raise VException(500, '选项配置错误')

        return attrs


# 更新字段
class CustomFieldUpdateSerializer(serializers.Serializer):
    is_required = serializers.BooleanField(required=True, error_messages={"required": "缺少是否必填", "invalid": "选择是否必填", "null": "是否必填不能为空"})
    label = serializers.CharField(required=True, error_messages={"required": "缺少字段名称", "blank": "字段名称不能为空", "null": "字段名称不能为空"})
    custom_field_options = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    enable = serializers.BooleanField(required=False, error_messages={"invalid": "选择是否启用", "null": "是否启用不能为空"})
    is_show = serializers.BooleanField(required=True, error_messages={"required": "缺少是否展示", "invalid": "选择是否展示", "null": "是否展示不能为空"})
    is_order = serializers.BooleanField(required=True, error_messages={"required": "缺少是否排序", "invalid": "选择是否排序", "null": "是否排序不能为空"})
    is_filter = serializers.BooleanField(required=True, error_messages={"required": "缺少是否筛选", "invalid": "选择是否筛选", "null": "是否筛选不能为空"})


    def validate_custom_field_options(self, attrs):
        if attrs:
            try:
                result = json.loads(attrs)
            except Exception as e:
                raise VException(500, '选项配置错误')

        return attrs