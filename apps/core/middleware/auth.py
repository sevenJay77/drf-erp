from rest_framework.authentication import BaseAuthentication
from core.framework.v_exception import VException
from permcontrol.models import User
from permcontrol.service import check_cache_token
from permcontrol.service import get_cache_role_permission


class CommonAuthentication(BaseAuthentication):

    def authenticate(self, request):
        # header获取Token
        access_token = request.META.get('HTTP_ACCESS_TOKEN', '')
        if not access_token:
            raise VException(401, "当前未登录")
        # 校验缓存里的token
        user_id = check_cache_token(access_token)
        # 用户校验
        user = User.objects.filter(id=user_id,
                                   is_delete=0).first()
        if not user:
            raise VException(401, "用户未注册")
        # 缓存角色、权限
        user_role, user_perms = get_cache_role_permission(user)
        user.role = user_role
        user.permission = user_perms
        result = (user,  None)
        return result