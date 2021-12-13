from django_filters import rest_framework as filters
from warehouse.models import Warehouse, Product



class WarehouseFilter(filters.FilterSet):
    code = filters.CharFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Warehouse
        fields = ["code", "name"]



class ProductFilter(filters.FilterSet):
    code = filters.CharFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["code", "name"]