from rest_framework.routers import DefaultRouter
from common.views import CustomFieldView

common_router = DefaultRouter()
common_router.register("custom_field", CustomFieldView, base_name="custom_field")
