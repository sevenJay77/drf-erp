from django_filters import rest_framework as filters
from permcontrol.models import PermissionGroup, Role, Department, User
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


class UserFilter(filters.FilterSet):
    status = filters.NumberFilter(lookup_expr="exact")
    display_name = filters.CharFilter(lookup_expr="icontains")
    department_id = filters.NumberFilter(method="department_filter")
    mobile = filters.CharFilter(method='mobile_filter')
    superior_id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = User
        fields = ["status", "display_name", "department_id", "mobile", "superior_id"]

    def mobile_filter(self, queryset, field_name, value):
        return queryset.filter(Q(mobile__icontains=value) | Q(private_mobile__icontains=value)).distinct()

    def department_filter(self, queryset, field_name, value):
        department_list = [value]
        child_department = Department.objects.filter(parent_id=value,
                                                     is_delete=0).all()
        for child in child_department:
            department_list.append(child.id)

        return queryset.filter(department_id__in=department_list)
