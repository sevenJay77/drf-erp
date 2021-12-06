from rest_framework.fields import CharField, DateField, TimeField, IntegerField, BooleanField, FileField, FloatField, \
    DateTimeField, ChoiceField
from core.framework.v_exception import VException

from common.models import CustomField
import logging

logger = logging.getLogger("django")
# 自定义字段校验
custom_type_list = ['CharField', 'DateField', 'TimeField', 'IntegerField', 'BooleanField', 'FileField', 'FloatField',
                    'DateTimeField', 'ChoiceField']


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
    attrs['custom_dict'] = custom_dict
    return attrs


# 校验
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
