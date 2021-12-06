import re
import random

from rest_framework.response import Response
from collections import OrderedDict
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import EmptyPage


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
        diy_count = self.count
        return OrderedDict([
            ('count', diy_count),
            ('results', data)
        ])