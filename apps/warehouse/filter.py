from django_filters import rest_framework as filters
from warehouse.models import Warehouse, ProductCategory, Product



class WarehouseFilter(filters.FilterSet):
    code = filters.CharFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Warehouse
        fields = ["code", "name"]



class ProductCategoryFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    parent_id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = ProductCategory
        fields = ["name", "parent_id"]



class ProductFilter(filters.FilterSet):
    code = filters.CharFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")
    category_id = filters.NumberFilter(lookup_expr="exact")
    delivery_place = filters.CharFilter(lookup_expr="icontains")
    steel_mill = filters.CharFilter(lookup_expr="icontains")
    heat_number = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["code", "name", "category_id", "delivery_place", "steel_mill", "heat_number"]