from permcontrol.views import UserBasicView, RoleView, PermissionView, PersonalInfoView, DepartmentView, UserView, WOServiceView, AttendanceView
from rest_framework.routers import DefaultRouter

permcontrol_router = DefaultRouter()
permcontrol_router.register("account", UserBasicView, basename="basic")
permcontrol_router.register("permission", PermissionView, basename="permission")
permcontrol_router.register("role", RoleView, basename="role")
permcontrol_router.register("department", DepartmentView, basename="department")
permcontrol_router.register("account", PersonalInfoView, basename="info")
permcontrol_router.register("user", UserView, basename="user")
permcontrol_router.register("wo", WOServiceView, basename="wo")
permcontrol_router.register("attendance", AttendanceView, basename="attendance")
