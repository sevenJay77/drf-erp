from rest_framework.routers import DefaultRouter
from operate_record.views import UserNotifyView, AdminUserNotifyView

operate_router = DefaultRouter()
operate_router.register("admin_notify", AdminUserNotifyView, basename="admin_notify")
operate_router.register("user_notify", UserNotifyView, basename="user_notify")