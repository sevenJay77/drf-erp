import random
from core.utils.mysql_client import MysqlPoolInstance
from django.db.backends.mysql.base import DatabaseWrapper as _DatabaseWrapper
import MySQLdb
from django.db.backends.base.base import BaseDatabaseWrapper

class DatabaseWrapper(_DatabaseWrapper):

    # 使用Pool连接池
    def get_new_connection(self, conn_params):
        conn_params['creator'] = MySQLdb
        g_pool_connection = MysqlPoolInstance.get_storage_instance(conn_params)
        conn = g_pool_connection.get_conn()
        return conn

    # 覆盖掉原来的close方法，查询结束后连接不会自动关闭
    def _close(self):
        return None

    # 重写父类方法为空方法，因为PooledDB的conn没有autocommit属性，不重写就会报错
    def _set_autocommit(self, autocommit):
        pass
