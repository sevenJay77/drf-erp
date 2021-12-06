from django_filters import rest_framework as filters
from operate_record.models import NotifyMessage

class NotifyFilter(filters.FilterSet):
    is_read = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = NotifyMessage
        fields = ['is_read']

