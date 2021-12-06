from permcontrol.views import UserBasicView, RoleView, PermissionView, PersonalInfoView, DepartmentView, UserView, UserCustomFieldView
from rest_framework.routers import DefaultRouter

permcontrol_router = DefaultRouter()
permcontrol_router.register("account", UserBasicView, base_name="basic")
permcontrol_router.register("permission", PermissionView, base_name="permission")
permcontrol_router.register("role", RoleView, base_name="role")
permcontrol_router.register("department", DepartmentView, base_name="department")
permcontrol_router.register("account", PersonalInfoView, base_name="info")
permcontrol_router.register("user", UserView, base_name="user")
permcontrol_router.register("custom_field/user", UserCustomFieldView, base_name="custom_field_user")
