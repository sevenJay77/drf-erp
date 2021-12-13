from rest_framework.routers import DefaultRouter
from warehouse.views import WarehouseView, ProductView

warehouse_router = DefaultRouter()
warehouse_router.register("warehouse", WarehouseView, basename="warehouse")
warehouse_router.register("product", ProductView, basename="product")
