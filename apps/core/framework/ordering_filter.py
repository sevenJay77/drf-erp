import re
from rest_framework.filters import OrderingFilter



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
