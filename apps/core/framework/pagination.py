import re
import random

from rest_framework.response import Response
from collections import OrderedDict
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import EmptyPage

'''
example list默认 is_recommend  created_time  id 排序
传id的值，则是按照 -is_recommend    =is_recommend, -created_time, -id   =is_recommend, =created_time, -id
 
'''
# 递归查询
def filter_condition(params, record):
    key_list = []
    def filter_function(params_list):
        if len(params_list) == 0:
            return
        # 筛选条件
        condition = Q()
        condition.connector = 'AND'
        copy_list = params_list.copy()
        for index in range(len(copy_list)):
            value = copy_list[index]
            copy_value = value.strip('-')
            # 获取值
            record_value = getattr(record, copy_value)
            if index == len(copy_list) - 1:
                copy_value = copy_list[-1]
                # 根据排序规则判断
                if value.startswith('-'):
                    copy_value = "{}__lt".format(copy_value.strip('-'))
                else:
                    copy_value = "{}__gt".format(copy_value)
            condition.children.append((copy_value, record_value))
        key_list.append(condition)
        params_list.pop()
        filter_function(params_list)
    filter_function(params)
    return key_list


"""
自定义分页器类
"""
class StandardResultsSetPagination(PageNumberPagination):

    page_size = 10
    page_size_query_param = 'size'
    has_more = False
    is_app= False
    count = 0


    # 分页查询
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        # 分页大小
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        page_size = int(page_size)
        '''
        app下拉加载 传参 app_cursor -> 上一页最后记录的id
        '''
        app_load_param = request.query_params.get('app_cursor', None)
        if app_load_param is not None:
            self.is_app = True
            if not app_load_param.isdigit():
                raise ValueError()
            app_param = int(app_load_param)
            if app_param > 0:
                # 获取数据库中id的数据
                last_record = queryset.filter(id=app_param).first()
                if last_record:
                    # 排序参数
                    order_params = getattr(view, 'ordering', None)
                    ORDER_PATTERN = re.compile(r'\?|[-+]?[.\w]+$')
                    params_list = [term for term in order_params if ORDER_PATTERN.match(term)]
                    # 查询参数
                    condition_list = filter_condition(params_list, last_record)
                    condition = Q()
                    # 规则之间使用OR关联
                    for each in condition_list:
                        condition.add(each, 'OR')
                    print(condition)
                    queryset = queryset.filter(condition)

            # 加载更多
            if queryset.count() > page_size:
                self.has_more = True
            queryset = queryset[:page_size]
            return list(queryset)

        else:
            paginator = self.django_paginator_class(queryset, page_size)
            self.count = paginator.count
            page_number = request.query_params.get(self.page_query_param, 1)
            if page_number in self.last_page_strings:
                page_number = paginator.num_pages
            try:
                self.page = paginator.page(page_number)
                return list(self.page)
            except EmptyPage:
                return []


    # 分页响应返回
    def get_paginated_response(self, data):
        # app 返回
        result = self.get_paginated_data(data)
        return Response({"data": result})


    # 获取返回值
    def get_paginated_data(self, data):
        if self.is_app:
            return OrderedDict([
                ('has_more', self.has_more),
                ('results', data)
            ])
        else:
            diy_count = self.count
            return OrderedDict([
                ('count', diy_count),
                ('results', data)
            ])