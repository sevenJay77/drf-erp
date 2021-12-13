import json
from collections import OrderedDict
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from django.db import transaction
from django.db import models
from rest_framework.fields import empty, CharField, DateField, TimeField, IntegerField, BooleanField, FileField, FloatField, \
    DateTimeField, ChoiceField
from core.framework.v_exception import VException
from common.models import CustomField
import logging

logger = logging.getLogger("django")
# 自定义字段校验
custom_type_list = ['CharField', 'DateField', 'TimeField', 'IntegerField', 'BooleanField', 'FileField', 'FloatField',
                    'DateTimeField', 'ChoiceField']


# 通用类
class StandardModel(models.Model):
    is_delete = models.SmallIntegerField(choices=((0, '否'), (1, '是')), default=0)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_user_id = models.IntegerField(null=True)
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    update_user_id = models.IntegerField(null=True)
    custom_value = models.JSONField(null=True)

    class Meta:
        abstract = True



# 通用类
class StandardSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, help_text='id')
    create_user_id = serializers.IntegerField(read_only=True, help_text='创建用户id')
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text='创建时间')
    update_user_id = serializers.IntegerField(read_only=True, help_text='更新用户id')
    updated_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text='更新时间')

    class Meta:
        model = None
        table = ""

    # 系统字段序列化
    def to_custom_field(self):
        data = []
        fields = self._readable_fields
        for field in fields:
            # 过滤
            field_name = field.field_name
            if field_name == "custom_value":
                continue
            info = {
                "name": field_name,
                "label": field.help_text,
                "field_type": field.__class__.__name__,
                "read_only": field.read_only,
                "custom_field_options": None,
                "enable": True,
                "is_required": not field.allow_null,
                "is_default": True,
                "is_show": True,
                "position": 0
            }
            # 选择属性
            if hasattr(field, 'choices'):
                info['custom_field_options'] = json.dumps(field.choices, ensure_ascii=False)
            data.append(info)
        return data


    # 校验
    def validate(self, attrs):
        table = self.Meta.table
        form_data = self.initial_data.copy()
        attrs = validate_custom_dict(table, attrs, form_data)
        return attrs

    # 序列化输出
    def to_representation(self, instance):
        table = self.Meta.table
        # 通用字段
        ret = OrderedDict()
        fields = self._readable_fields
        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)
        # 自定义字段
        custom_value = ret.pop("custom_value", {})
        custom_fields = CustomField.objects.filter(is_delete=0,
                                                   table=table,
                                                   enable=1,
                                                   is_default=0).all()
        for custom_field in custom_fields:
            ret[custom_field.name] = custom_value.get(custom_field.name, None)
        return ret


# 自定义字段校验
def validate_custom_dict(table, attrs, form_data):
    # 校验自定义字段
    custom_dict = {}
    custom_fields = CustomField.objects.filter(is_delete=0,
                                               table=table,
                                               is_default=0,
                                               enable=1).all()
    for custom_field in custom_fields:
        field_name = custom_field.name
        custom_val = check_custom_ser(custom_field, form_data)
        custom_dict[field_name] = custom_val
    # 负责json字段
    attrs['custom_value'] = custom_dict
    return attrs


# 扩展字段校验
def check_custom_ser(custom_field, form_data):
    try:
        # 自定义类型
        field_name = custom_field.name
        field_type = custom_field.field_type
        field_label = custom_field.label
        is_required = not custom_field.is_required
        ser_class = globals()[field_type]
        ser_field = ser_class(required=True, allow_blank=is_required, allow_null=is_required,
                              error_messages={"required": "缺少{}".format(field_label),
                                              "null": "{}不能为空".format(field_label),
                                              "blank": "{}不能为空".format(field_label),
                                              "invalid": "{}格式错误".format(field_label)})
    except Exception as e:
        logging.error('error {}'.format(e))
        raise VException(500, '自定义字段校验错误')
    if is_required and field_name not in form_data.keys():
        raise VException(500, '缺少{}'.format(field_label))
    value = form_data.get(field_name, None)
    ser_field.run_validation(value)
    return value




