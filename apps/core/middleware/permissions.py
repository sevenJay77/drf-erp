from rest_framework.permissions import DjangoModelPermissions
from core.framework.v_exception import VException, PermissException
from permcontrol.service import get_permissions_role

import logging

logger = logging.getLogger("django")


'''
权限验证类
'''
class CustomPermissions(DjangoModelPermissions):
    # 提示信息
    message = '沒有操作权限'

    # 权限判断
    def has_permission(self, request, view):
        if view.action is None:
            raise VException(404, '请求路由不存在')

        try:
            user_perms = request.user.permission
            # 权限名称
            module_perms = view.module_perms
            action_perms = view.action
            # 默认权限
            if action_perms in ["list", "retrieve"] or action_perms in getattr(view, 'retrieve_perms', []):
                action_perms = "retrieve"
            elif action_perms in ["update", "partial_update"] or action_perms in getattr(view, 'edit_perms', []):
                action_perms = "edit"
            elif action_perms in ["destroy"]:
                action_perms = "delete"
            elif action_perms in  ["create"]:
                action_perms = "create"
            need_perms = "{}.{}".format(module_perms[0], action_perms)
        except:
            raise VException(500, '请求异常，请稍后再试')
        logger.info("need_perms {}".format(need_perms))
        if need_perms not in user_perms:
            # 查找权限所需的角色
            roles = get_permissions_role(need_perms)
            raise PermissException(403, "没有权限访问", roles)

        return True
