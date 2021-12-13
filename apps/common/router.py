from rest_framework.routers import DefaultRouter
from common.views import ResourceUploadView, CustomFieldView, CustomFieldListView

common_router = DefaultRouter()
common_router.register("resource", ResourceUploadView, basename="resource_upload")
common_router.register("custom_field", CustomFieldView, basename="custom_field")
common_router.register("get_custom_field", CustomFieldListView, basename="get_custom_field")
