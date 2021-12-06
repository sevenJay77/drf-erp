import datetime
import random
import json
from interval import Interval
import calendar
from django.db.models import Q

from config.config import SafeModuleConfig
from core.utils.redis_client import RedisClientInstance
from core.framework.v_exception import VException, KException
from permcontrol.models import Role, User, PermissionGroup
from warehouse.models import Warehouse
import logging

logger = logging.getLogger("django")


# 清除token缓存
def clean_user_expire_token(access_token):
    if not access_token:
        return
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'token_expire:user_token:{}'.format(access_token)
        redis_client.delete_by_name(cache_key)
    except:
        raise VException(500, "服务器正忙，请稍后再试")


# 更新token缓存
def cache_user_expire_token(access_token, user_id, time_now):
    if not access_token:
        return
    expire_time = 60 * SafeModuleConfig.access_token_exp
    refresh_time = 60 * SafeModuleConfig.access_token_refresh_exp
    now_timestamp = int(time_now.timestamp())
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'token_expire:user_token:{}'.format(access_token)
        cache_value = {
            'user_id': user_id,
            'expire_time': now_timestamp + expire_time
        }
        # 更新缓存
        redis_client.single_set_string_with_expire_time(cache_key, 'second', refresh_time, json.dumps(cache_value))
    except Exception as e:
        raise VException(500, "服务器正忙，请稍后再试")


def check_cache_token(access_token):
    '''
    缓存创建时间、失效时间
    如果超过失效时间, 刷新有效期
    '''
    if not access_token:
        return None
    user_id = None
    expire_time = None
    time_now = datetime.datetime.now()
    now_timestamp = int(time_now.timestamp())
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'token_expire:user_token:{}'.format(access_token)
        cache_value = redis_client.get_by_name(cache_key)
        if cache_value:
            value = json.loads(cache_value)
            user_id = value.get('user_id', None)
            expire_time = value.get('expire_time', None)
    except:
        raise VException(500, "服务器正忙，请稍后再试")
    if not user_id or not expire_time:
        raise VException(401, "登录已失效")
    # 刷新token
    if now_timestamp > expire_time:
        cache_user_expire_token(access_token, user_id, time_now)
    return user_id


# 获取权限
def init_role_permissions(user):
    role_name = None
    perms_name_list = []
    # 获取所有角色
    role = Role.objects.filter(id=user.role_id,
                               is_delete=0).first()

    if role:
        for per in role.permission.all():
            perms_name_list.append(per.action)
        # 去重
        perms_name_list = list(set(perms_name_list))
        perms_name_list.sort()

        role_name = role.name
    return role_name, perms_name_list


# 查找权限所需的角色
def get_permissions_role(need_perms):
    role_name_list = []
    need_role = Role.objects.filter(permission__action=need_perms,
                                    is_delete=0).all()
    for role in need_role:
        role_name_list.append(role.name)
    role_name_list = list(set(role_name_list))
    return role_name_list


# 缓存权限
def get_cache_role_permission(user):
    if not user:
        return None, []
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        cache_key = 'permissions_cache:user_role:{}'.format(user.id)
        cache_value = redis_client.get_by_name(cache_key)
        if cache_value is None:
            # 随机失效时间
            expire_time = random.randint(1, 10) * 60 + 3 * 60 * 60
            # 缓存权限组
            role, perms_list = init_role_permissions(user)
            role_perms = {
                'role': role,
                'permission': perms_list
            }
            redis_client.single_set_string_with_expire_time(cache_key, 'second', expire_time, json.dumps(role_perms))
        else:
            # 解码权限组
            role_perms = json.loads(cache_value)
            role = role_perms.get('role', None)
            perms_list = role_perms.get('permission', [])
    except Exception as e:
        logger.error("init permission error {}".format(e))
        raise VException(500, "服务器正忙，请稍后再试")

    return role, perms_list


# 清空用户角色、权限缓存
def clean_cache_role_permission(user_ids):
    # 判断是否为数组
    if not isinstance(user_ids, list):
        raise VException(500, "操作失败")
    if len(user_ids) == 0:
        return
    # 清空权限
    try:
        redis_client = RedisClientInstance.get_storage_instance()
        for user_id in user_ids:
            cache_key = 'permissions_cache:user_role:{}'.format(user_id)
            redis_client.delete_by_name(cache_key)
    except Exception as e:
        logger.error("clean permission error {}".format(e))
        raise VException(500, "操作失败，服务器正忙，请稍后再试")


# 删除用户关联数据
def clean_user_related_data(user_id):
    # 主管关联置空
    sub_list = User.objects.filter(superior_id=user_id,
                                   is_delete=0).all()
    for sub in sub_list:
        sub.superior_id = None
        sub.save()

    # 仓库管理员
    warehouse_list = Warehouse.objects.filter(manager_id=user_id,
                                              is_delete=0).all()
    for warehouse in warehouse_list:
        warehouse.manager_id = None
        warehouse.save()


# 获取权限的所有父级
def get_full_tree_permission(permission_id):
    permission_list = []

    def get_parent_permission(parent_id):
        permission = PermissionGroup.objects.filter(id=parent_id).first()
        if not permission:
            raise VException(500, "所选权限不存在")
        permission_list.append(permission.id)
        if permission.parent_id:
            get_parent_permission(permission.parent_id)

    get_parent_permission(permission_id)
    return permission_list