from django_filters import rest_framework as filters
from permcontrol.models import PermissionGroup, Role, Department
from django.db.models import Q


class PermissionFilter(filters.FilterSet):
    parent_id = filters.NumberFilter(lookup_expr="exact")
    type = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = PermissionGroup
        fields = ["type", "parent_id"]


class RoleFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Role
        fields = ["name"]


class DepartmentFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    parent_id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = Department
        fields = ["name", "parent_id"]

