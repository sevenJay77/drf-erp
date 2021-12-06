from django.urls import path, include
from django.conf.urls import url, re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from swallow.settings import MEDIA_ROOT, STATIC_ROOT
from core.framework.error_page import page_not_found, server_error

# 自定义路由
from permcontrol.router import permcontrol_router
from warehouse.router import warehouse_router
from common.router import common_router

# 添加路由
route = DefaultRouter()
route.registry.extend(permcontrol_router.registry)
route.registry.extend(edition_router.registry)
route.registry.extend(warehouse_router.registry)
route.registry.extend(common_router.registry)


schema_view = get_schema_view(
    openapi.Info(
        title="DRF-ERP API Doc",
        default_version='v1',
    ),
    public=True,
    permission_classes=(AllowAny,),
    authentication_classes=()
)


urlpatterns = [
    re_path(r"^api/", include(route.urls)),
    # swagger
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0)),
    # media 配置
    url(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
    # 静态资源配置
    re_path(r'^static(?P<path>.*)$', serve, {'document_root': STATIC_ROOT}),
]

handler404 = page_not_found
handler500 = server_error