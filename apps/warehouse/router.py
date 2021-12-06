from rest_framework.routers import DefaultRouter
from warehouse.views import WarehouseView, ProductCategoryView, ProductView

warehouse_router = DefaultRouter()
warehouse_router.register("warehouse", WarehouseView, base_name="warehouse")
warehouse_router.register("product_category", ProductCategoryView, base_name="product_category")
warehouse_router.register("product", ProductView, base_name="product")
