import datetime
import random
import json
from interval import Interval
import calendar
from django.db.models import Q

from config.config import SafeModuleConfig
from core.utils.redis_client import RedisClientInstance
from core.framework.v_exception import VException, KException
from permcontrol.models import Role, User, PermissionGroup, AdmitRecord, AttendanceRecord, CalendarEditRecord, AttendanceConfig
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



# 编辑配置考勤
def edit_attendance_config(form_data, user):
    time_interval_tuple = form_data['time_interval_tuple']
    out_limit = form_data['out_limit']
    exclude_user = form_data['exclude_user']
    # 更新时间区域
    setting = AttendanceConfig()
    setting.name = 'time_interval_tuple'
    setting.value = json.dumps(time_interval_tuple)
    setting.date = datetime.datetime.now()
    setting.create_user_id = user.id
    setting.update_user_id = user.id
    setting.save()
    # 更新超时时间
    setting = AttendanceConfig()
    setting.name = 'out_limit'
    setting.value = out_limit
    setting.date = datetime.datetime.now()
    setting.create_user_id = user.id
    setting.update_user_id = user.id
    setting.save()
    # 更新人员
    setting = AttendanceConfig()
    setting.name = 'exclude_user'
    setting.value = exclude_user
    setting.date = datetime.datetime.now()
    setting.create_user_id = user.id
    setting.update_user_id = user.id
    setting.save()


# 获取考勤配置
def get_attendance_config(date:datetime.datetime):
    attendance_config = {
        'time_interval_tuple': None,
        'out_limit': None,
        'exclude_user': []
    }
    time_interval_tuple_config = AttendanceConfig.objects.filter(Q(name='time_interval_tuple'),
                                                                ~Q(date__gte=date)).order_by('-id').first()
    if time_interval_tuple_config:
        try:
            time_interval_tuple = json.loads(time_interval_tuple_config.value)
            attendance_config['time_interval_tuple'] = time_interval_tuple
        except:
            logger.error("attendance config error {}".format(time_interval_tuple_config))
            raise VException(500, '上班时间段配置错误')

    out_limit_config = AttendanceConfig.objects.filter(Q(name='out_limit'),
                                                       ~Q(date__gte=date)).order_by('-id').first()
    if out_limit_config:
        try:
            out_limit = out_limit_config.value
            attendance_config['out_limit'] = float(out_limit)
        except:
            logger.error("attendance config error {}".format(out_limit_config))
            raise VException(500, '外出时长配置错误')

    exclude_user_config = AttendanceConfig.objects.filter(Q(name='exclude_user')).order_by('-id').first()
    if exclude_user_config:
        try:
            exclude_user = exclude_user_config.value
            if exclude_user:
                attendance_config['exclude_user'] = exclude_user.split(',')
        except:
            logger.error("attendance config error {}".format(out_limit_config))
            raise VException(500, '考勤人员配置错误')
    return attendance_config


# 判断是否外出过长
def check_out_limit(out_duration, out_limit):
    if out_duration is None:
        out_duration = 0
    if out_duration >= out_limit:
        return 1

    return 0


# 计算规定上班总时长
def total_duty_time(time_interval_tuple):
    total_duty = 0
    for index in range(len(time_interval_tuple)):
        interval = time_interval_tuple[index]
        # 上班区间时长
        duty_interval = datetime.datetime.strptime(interval[1], "%H:%M") - datetime.datetime.strptime(interval[0], "%H:%M")
        interval_hours = round(duty_interval.seconds / 3600, 2)
        total_duty += interval_hours

    return total_duty


# 数据库打卡数据
def summary_database_function(user, input_datetime:datetime.datetime, time_interval_tuple, out_limit):
    # 初始化数据
    info = {
        'user_id': user.id,
        'name': user.display_name,
        'job_number': user.job_number,
        'date': input_datetime.strftime('%Y-%m-%d'),
        'record_list': [],
        'origin_first_admit': None,
        'origin_last_admit': None,
        'origin_out_duration': 0,
        'origin_duty_duration': 0,
        'first_admit': None,
        'last_admit': None,
        'out_duration': None,
        'duty_duration': None,
        'result_out_duration': 0,
        'result_duty_duration': 0,
        'valid_duty_duration': 0,
        'is_late': 0,
        'is_leave_early': 0,
        'is_out_timeout': 0,
    }

    # 获取门禁数据
    record_list = []
    admit_record = AdmitRecord.objects.filter(Q(user_id=user.id) | Q(admit_guid=user.admit_guid),
                                              show_time__year=input_datetime.year,
                                              show_time__month=input_datetime.month,
                                              show_time__day=input_datetime.day).order_by("show_time")
    for record in admit_record:
        record_list.append({
            'admit_type': record.admit_type,
            'show_time': record.show_time.strftime('%H:%M:%S')
        })
    info['record_list'] = record_list

    # 原始记录
    origin_record = AttendanceRecord.objects.filter(user_id=user.id,
                                                    date=input_datetime,
                                                    is_revise=0).first()
    if origin_record:
        # 加载配置信息
        info['origin_first_admit'] = origin_record.first_admit
        info['origin_last_admit'] = origin_record.last_admit
        info['origin_out_duration'] = origin_record.out_duration
        info['origin_duty_duration'] = origin_record.duty_duration
        info['result_out_duration'] = origin_record.out_duration
        info['result_duty_duration'] = origin_record.duty_duration
        info['is_late'] = origin_record.is_late
        info['is_leave_early'] = origin_record.is_leave_early
        info['is_out_timeout'] = origin_record.is_out_timeout

    else:
        out_duration = 0
        # 计算实时数据
        if len(record_list) > 0:
            info['origin_first_admit'] = record_list[0]['show_time']
            info['origin_last_admit'] = record_list[-1]['show_time']
            # 日期格式化
            first_admit = datetime.datetime.strptime(record_list[0]['show_time'], '%H:%M:%S')
            last_admit = datetime.datetime.strptime(record_list[-1]['show_time'], '%H:%M:%S')
            # 计算
            result = check_summary_attendance(first_admit, last_admit, time_interval_tuple)
            info['is_late'] = result['is_late']
            info['is_leave_early'] = result['is_leave_early']
            info['origin_duty_duration'] = result['duty_duration']
            # 获取统计结果
            interval_list = result['interval_list']
            for interval in interval_list:
                total_out = summary_out(record_list, interval[0], interval[1])
                out_duration += total_out
            out_duration = round(out_duration, 2)
            info['origin_out_duration'] = out_duration
            info['result_out_duration'] = out_duration
            info['result_duty_duration'] = result['duty_duration']
            info['is_out_timeout'] = check_out_limit(out_duration, out_limit)

        # 如果不是当天数据，则入库
        time_now = datetime.datetime.now()
        today_now_datetime = datetime.datetime(time_now.year, time_now.month, time_now.day)
        if input_datetime < today_now_datetime:
            new_record = AttendanceRecord()
            new_record.code =  "{}{}".format(input_datetime.strftime('%Y%m%d'), user.id)
            new_record.user_id = user.id
            new_record.date = input_datetime
            new_record.first_admit = info['origin_first_admit']
            new_record.last_admit = info['origin_last_admit']
            new_record.out_duration = out_duration
            new_record.duty_duration = info['result_duty_duration']
            new_record.is_late = info['is_late']
            new_record.is_leave_early = info['is_leave_early']
            new_record.is_out_timeout = info['is_out_timeout']
            new_record.time_interval_tuple = json.dumps(time_interval_tuple)
            new_record.out_limit = out_limit
            new_record.is_revise = 0
            new_record.save()

    # 修正记录
    revise_record = AttendanceRecord.objects.filter(user_id=user.id,
                                                    date=input_datetime,
                                                    is_revise=1).first()
    if revise_record:
        info['first_admit'] = revise_record.first_admit
        info['last_admit'] = revise_record.last_admit
        info['out_duration'] = revise_record.out_duration
        info['duty_duration'] = revise_record.duty_duration
        info['is_late'] = revise_record.is_late
        info['is_leave_early'] = revise_record.is_leave_early
        info['is_out_timeout'] = revise_record.is_out_timeout
        info['result_duty_duration'] = revise_record.duty_duration
        if revise_record.out_duration is None:
            info['result_out_duration'] = origin_record.out_duration
        else:
            info['result_out_duration'] = revise_record.out_duration
    info['valid_duty_duration'] = round(info['result_duty_duration'] - info['result_out_duration'], 2)

    return info


# 生成统计记录
def generate_origin_database(user, date, time_interval_tuple, out_limit):
    # 不生成未来统计
    time_now = datetime.datetime.now()
    today_now_datetime = datetime.datetime(time_now.year, time_now.month, time_now.day)
    if date >= today_now_datetime:
        return
    code = "{}{}".format(date.strftime('%Y%m%d'), user.id)
    new_record = AttendanceRecord.objects.filter(code=code,
                                                 is_revise=0).first()
    if not new_record:
        new_record = AttendanceRecord()

    # 获取门禁数据
    record_list = []
    admit_record = AdmitRecord.objects.filter(Q(user_id=user.id) | Q(admit_guid=user.admit_guid),
                                              show_time__year=date.year,
                                              show_time__month=date.month,
                                              show_time__day=date.day).order_by("show_time")
    for record in admit_record:
        record_list.append({
            'admit_type': record.admit_type,
            'show_time': record.show_time.strftime('%H:%M:%S')
        })

    new_record.code = "{}{}".format(date.strftime('%Y%m%d'), user.id)
    new_record.date = date
    new_record.user_id = user.id
    new_record.is_late = 0
    new_record.is_leave_early = 0
    out_duration = 0

    if len(record_list):
        first_admit = datetime.datetime.strptime(record_list[0]['show_time'], '%H:%M:%S')
        last_admit = datetime.datetime.strptime(record_list[-1]['show_time'], '%H:%M:%S')
        # 计算
        new_record.first_admit = first_admit
        new_record.last_admit = last_admit
        result = check_summary_attendance(first_admit, last_admit, time_interval_tuple)
        new_record.is_late = result['is_late']
        new_record.is_leave_early = result['is_leave_early']
        new_record.origin_duty_duration = result['duty_duration']
        new_record.duty_duration = result['duty_duration']
        # 获取统计结果
        interval_list = result['interval_list']
        for interval in interval_list:
            total_out = summary_out(record_list, interval[0], interval[1])
            out_duration += total_out
        out_duration = round(out_duration, 2)
    new_record.out_duration = out_duration
    new_record.is_out_timeout = check_out_limit(out_duration, out_limit)
    new_record.is_revise = 0
    new_record.time_interval_tuple = json.dumps(time_interval_tuple)
    new_record.out_limit = out_limit
    new_record.save()



# 生成修正记录
def generate_revise_database(origin_record, revise_record, form_data):
    first_admit = form_data.get('first_admit', None)
    last_admit = form_data.get('last_admit', None)
    out_duration = form_data.get('out_duration', None)
    # 都为空则不做修改
    if first_admit is None and last_admit is None and out_duration is None:
        logger.info('revise no data')
        return
    # 考勤时间
    origin_first_admit = origin_record.first_admit
    origin_last_admit = origin_record.last_admit
    # 配置信息
    time_interval_tuple = json.loads(origin_record.time_interval_tuple)
    out_limit = origin_record.out_limit
    # 修正时间
    if first_admit is None:
        first_admit = origin_first_admit
    if last_admit is None:
        last_admit = origin_last_admit
    # 判断数据类型
    if first_admit and last_admit is None:
        first_admit = datetime.datetime.strptime(first_admit.strftime('%H:%M:%S'), '%H:%M:%S')
        last_admit = first_admit
    elif first_admit is None and last_admit:
        last_admit = datetime.datetime.strptime(last_admit.strftime('%H:%M:%S'), '%H:%M:%S')
        first_admit = last_admit
    elif first_admit and last_admit:
        first_admit = datetime.datetime.strptime(first_admit.strftime('%H:%M:%S'), '%H:%M:%S')
        last_admit = datetime.datetime.strptime(last_admit.strftime('%H:%M:%S'), '%H:%M:%S')

    # 计算
    result = check_summary_attendance(first_admit, last_admit, time_interval_tuple)
    revise_record.is_late = result['is_late']
    revise_record.is_leave_early = result['is_leave_early']
    revise_record.origin_duty_duration = result['duty_duration']
    revise_record.duty_duration = result['duty_duration']
    if revise_record.out_duration is None:
        revise_record.is_out_timeout= check_out_limit(origin_record.out_duration, out_limit)
    else:
        revise_record.is_out_timeout= check_out_limit(revise_record.out_duration, out_limit)

    revise_record.save()

# 判断迟到、早退、工作时间 datetime
def check_summary_attendance(first_admit_time, last_admit_time, time_interval_tuple):
    result = {
        'is_late': 0,
        'is_leave_early': 0,
        'duty_duration': 0,
        'interval_list': []
    }

    if last_admit_time is None and last_admit_time is None:
        return result

    if last_admit_time < first_admit_time:
        return result

    try:
        # 有效时区
        morning_start_time = datetime.datetime.strptime(time_interval_tuple[0][0], "%H:%M")
        morning_end_time = datetime.datetime.strptime(time_interval_tuple[0][1], "%H:%M")
        afternoon_start_time = datetime.datetime.strptime(time_interval_tuple[1][0], "%H:%M")
        afternoon_end_time = datetime.datetime.strptime(time_interval_tuple[1][1], "%H:%M")

        # 节点判断
        # 打卡时区还包括迟到，早退
        if first_admit_time > afternoon_end_time or last_admit_time < morning_start_time:
            # 1. 签到打卡在下班后
            # 2. 签退在上班前
            # 缺勤 工作时间 0， 外出时间 0
            is_late = 1
            is_leave_early = 1
            total_duty = 0
            interval_list = []
            # 添加异常判断
            if first_admit_time <= morning_start_time:
                is_late = 0
        elif last_admit_time in Interval(morning_start_time, afternoon_start_time):
            is_late = 0
            is_leave_early = 1
            # 在下午之前签退
            # 下午缺勤, 只计算上午的时间
            # 判断是否 迟到、早退
            if first_admit_time > morning_start_time:
                # 迟到
                is_late = 1
                today_start_time = first_admit_time
            else:
                today_start_time = morning_start_time
            if last_admit_time < morning_end_time:
                today_end_time = last_admit_time
            else:
                today_end_time = morning_end_time
            # 计算工作时间
            total_duty = (today_end_time - today_start_time).seconds
            interval_list = [(today_start_time, today_end_time)]

        elif first_admit_time in Interval(morning_end_time, afternoon_end_time):
            is_late = 1
            is_leave_early = 0
            # 在上午结束后打卡
            # 上午缺勤
            if first_admit_time > afternoon_start_time:
                # 迟到
                today_start_time = first_admit_time
            else:
                today_start_time = afternoon_start_time

            if last_admit_time < afternoon_end_time:
                # 早退
                is_leave_early = 1
                today_end_time = last_admit_time
            else:
                today_end_time = afternoon_end_time
            # 计算工作时间
            total_duty = (today_end_time - today_start_time).seconds
            interval_list = [(today_start_time, today_end_time)]

        else:
            is_late = 0
            is_leave_early = 0
            interval_list = []
            # 正常上班
            if first_admit_time > morning_start_time:
                # 迟到
                is_late = 1
                today_start_time = first_admit_time
            else:
                today_start_time = morning_start_time

            today_end_time = morning_end_time
            # 单独计算上午
            morning_total_duty = (today_end_time - today_start_time).seconds
            interval_list.append((today_start_time, today_end_time))

            # 计算下午
            today_start_time = afternoon_start_time
            if last_admit_time < afternoon_end_time:
                # 早退
                is_leave_early = 1
                today_end_time = last_admit_time
            else:
                today_end_time = afternoon_end_time

            afternoon_total_duty = (today_end_time - today_start_time).seconds
            total_duty = morning_total_duty + afternoon_total_duty
            interval_list.append((today_start_time, today_end_time))

        total_duty = round(total_duty / 3600, 2)
        result = {
            'is_late': is_late,
            'is_leave_early': is_leave_early,
            'duty_duration': total_duty,
            'interval_list': interval_list
        }
        return result
    except Exception as e:
        logger.error("获取考勤结果 error {}".format(e))
        raise VException(500, "获取考勤结果错误")


# 统计时区内出去时长
def summary_out(admit_list, today_start_time, today_end_time):
    total_out = 0
    time_admit_list = []
    for out_admit in admit_list:
        show_time = datetime.datetime.strptime(out_admit['show_time'], "%H:%M:%S")
        # 过滤
        if show_time in Interval(today_start_time, today_end_time):
            time_admit_list.append(out_admit)

    # 寻找第一次出去的值
    out_record = None
    for out_admit in time_admit_list:

        if out_admit['admit_type'] == 1:
            out_record = out_admit
            continue

        # 一次完整的记录
        if out_record and out_admit['admit_type'] == 0:
            out_record_datetime = datetime.datetime.strptime(out_record['show_time'], "%H:%M:%S")
            in_record_datetime = datetime.datetime.strptime(out_admit['show_time'], "%H:%M:%S")
            if in_record_datetime < out_record_datetime:
                continue
            total_out += (in_record_datetime - out_record_datetime).seconds

        out_record = None
    total_out = round(total_out / 3600, 2)
    return total_out


# 获取考勤日历
def get_attendance_calendar(month_date:datetime.datetime):
    data = []
    year = month_date.year
    month = month_date.month
    # 计算当月天数
    num_days = calendar.monthrange(year, month)[1]
    # weekday 0-4 周一到周五    5,6 周六周天
    for day in range(1, num_days + 1):
        day_datetime = datetime.date(year, month, day)
        # 判断是否有修改记录
        record = CalendarEditRecord.objects.filter(day=day_datetime).first()
        if record:
            is_holiday = record.is_holiday
        else:
            weekday = day_datetime.weekday()
            if weekday <= 4:
                is_holiday = 0
            else:
                is_holiday = 1
        data.append({
            'day': day_datetime.strftime("%Y-%m-%d"),
            'is_holiday': is_holiday
        })
    return data

