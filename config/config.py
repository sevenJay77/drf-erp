# coding: utf-8


import os
from configobj import ConfigObj

# 配置文件
cfg_file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__))), "config.ini")
config = ConfigObj(cfg_file, encoding='UTF8')


class SettingsUtils:
    """
    读取项目配置文件
    """

    @staticmethod
    def get_val(section, key):
        """
        根据section和key获取值
        :param section: ini文件中section
        :param key: ini文件中key
        :return: 对应值
        """
        return config[section][key]


class CommonConfig:
    """
    Env配置
    """
    debug = SettingsUtils.get_val('env', 'debug')
    if debug == 'False':
        debug_mode = False
    else:
        debug_mode = True
    bind_port = SettingsUtils.get_val('env', 'bind_port')
    workers_number = int(SettingsUtils.get_val('env', 'workers_number'))
    threads_number = int(SettingsUtils.get_val('env', 'threads_number'))


    """
    Log配置
    """
    log_max_counts = int(SettingsUtils.get_val('log', 'log_max_counts'))

    """
    mysql配置
    """
    database_name = SettingsUtils.get_val('mysql', 'database_name')
    database_user = SettingsUtils.get_val('mysql', 'database_user')
    database_password = SettingsUtils.get_val('mysql', 'database_password')
    database_host = SettingsUtils.get_val('mysql', 'database_host')
    database_port = int(SettingsUtils.get_val('mysql', 'database_port'))

    """
    redis配置
    """
    redis_host = SettingsUtils.get_val('ai_redis', 'redis_host')
    redis_port = int(SettingsUtils.get_val('ai_redis', 'redis_port'))
    redis_password = SettingsUtils.get_val('ai_redis', 'redis_password')
    redis_position_db = SettingsUtils.get_val('ai_redis', 'redis_position_db')
    consumer_key = SettingsUtils.get_val('ai_redis', 'consumer_key')


class SafeModuleConfig:
    # token有效时间
    access_token_exp = int(SettingsUtils.get_val('safe_module', 'access_token_exp'))
    access_token_refresh_exp = int(SettingsUtils.get_val('safe_module', 'access_token_refresh_exp'))
    ip_verify_limit = int(SettingsUtils.get_val('safe_module', 'ip_verify_limit'))
    anon_time_request = SettingsUtils.get_val('safe_module', 'anon_time_request')
    user_time_request = SettingsUtils.get_val('safe_module', 'user_time_request')

