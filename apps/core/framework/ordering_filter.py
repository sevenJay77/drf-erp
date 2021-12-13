import re
from common.models import CustomField
from rest_framework.filters import OrderingFilter
from django_filters import FilterSet
import logging

logger = logging.getLogger("django")


# 自定义排序
class StandardOrdering(OrderingFilter):

    def format_params(self, params):
        if params.startswith('-'):
            params = params.strip('-')
        return params

    '''
    指定排序后，次级排序同样使用默认排序
    '''
    def get_ordering(self, request, queryset, view):
        ordering_params = None
        # 输入排序参数
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                ordering_params = ordering
        # 默认排序
        default_params = self.get_default_ordering(view)
        # 某一参数为空
        if not default_params or not ordering_params:
            return ordering_params or default_params

        # 拷贝数组
        copy_dict = list(default_params)
        for order_param in ordering_params:
            # 查找是否默认参数
            for match_param in default_params:
                reg_str = r'\?|[-+]?({})+$'.format(order_param)
                if re.search(reg_str, match_param):
                    copy_dict.remove(match_param)
                    break
        return_params = ordering_params + copy_dict
        return return_params




# 自定义扩展字段排序
class CustomStandardOrdering(OrderingFilter):

    # 获取自定义排序参数
    def get_custom_order_fields(self, fields, view):
        ORDER_PATTERN = re.compile(r'\?|[-+]?[.\w]+$')
        valid_fields = []
        ser_class = getattr(view, 'serializer_class', None)
        if ser_class is None:
            return valid_fields
        table = ser_class.Meta.table
        if table is None:
            return valid_fields

        # 获取配置字段
        config_fields = []
        order_queryset = CustomField.objects.filter(is_delete=0,
                                                    table=table,
                                                    enable=1,
                                                    is_order=1).all()
        for queryset in order_queryset:
            info = {
                'name': queryset.name,
                'is_default': queryset.is_default
            }

            config_fields.append(info)

        # 筛选
        for term in fields:
            for field in config_fields:
                if field['name'] == term.lstrip('-') and ORDER_PATTERN.match(term):
                    # 如果是自定义字段
                    if field['is_default'] == 0:
                        term = "custom_value__{}".format(term)
                    valid_fields.append(term)
                    break

        return valid_fields

    # 获取排序参数
    def get_ordering(self, request, queryset, view):
        input_params = None
        # 输入排序参数
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            input_params = self.get_custom_order_fields(fields, view)
        # 默认排序
        default_params = self.get_default_ordering(view)
        # 某一参数为空
        if not default_params or not input_params:
            return input_params or default_params
        # 拷贝数组
        copy_dict = list(default_params)
        for order_param in input_params:
            # 查找是否默认参数
            for match_param in default_params:
                reg_str = r'\?|[-+]?({})+$'.format(order_param)
                if re.search(reg_str, match_param):
                    copy_dict.remove(match_param)
                    break
        return_params = input_params + copy_dict
        return return_params


    # 获取自定义筛选参数
    def get_custom_filter_fields(self, view, params_dict):
        conditions  = {}
        ser_class = getattr(view, 'serializer_class', None)
        if ser_class is None:
            return conditions
        table = ser_class.Meta.table
        if table is None:
            return conditions
        # 获取配置项
        order_queryset = CustomField.objects.filter(is_delete=0,
                                                    table=table,
                                                    enable=1,
                                                    is_filter=1).all()
        for queryset in order_queryset:
            field_name = queryset.name
            field_type =  queryset.field_type
            # 如果是输入值
            if field_name in params_dict:
                # 字符串默认模糊查询
                if field_type == "CharField":
                    key = "custom_value__{}".format(field_name)
                    conditions[key] = params_dict[field_name]
                else:
                    conditions[field_name] = params_dict[field_name]
        return conditions


    # 获取筛选参数
    def get_filtering(self, request, view):
        conditions = None
        # 拼接筛选参数
        params_dict = {}
        query_params = request.query_params
        for key in query_params:
            params_dict[key.strip()] = query_params[key]
        # 格式化
        if params_dict:
            conditions = self.get_custom_filter_fields(view, params_dict)
        return conditions


    def filter_queryset(self, request, queryset, view):
        # 获取排序
        ordering = self.get_ordering(request, queryset, view)
        logger.info("result ordering {}".format(ordering))
        if ordering:
            queryset = queryset.order_by(*ordering)
        # 获取筛选参数
        filtering = self.get_filtering(request, view)
        logger.info("result filtering {}".format(filtering))
        if filtering:
            queryset = queryset.filter(**filtering)
        return queryset