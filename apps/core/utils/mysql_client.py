"""
MySQL操作类
"""
import MySQLdb
import threading
from config.config import CommonConfig
from dbutils.pooled_db import PooledDB

import logging
log = logging.getLogger("django")


# 用连接池来返回数据库连接
class DMysqlPoolConn:

    def __init__(self, config):
       self.__pool = PooledDB(**config)

    def get_conn(self):
        return self.__pool.connection()



class MysqlPoolInstance(object):
    # 线程锁
    _instance_lock = threading.Lock()

    def __init__(self, *args,**kwargs):
        pass

    @classmethod
    def get_storage_instance(cls, connect_params):
        if not hasattr(MysqlPoolInstance,'_instance'):
            with MysqlPoolInstance._instance_lock:
                MysqlPoolInstance._instance = DMysqlPoolConn(connect_params)

            log.info('================= mysql client instance  =====================')
        return MysqlPoolInstance._instance



# 使用 with 的方式来优化代码
class UsingMysql(object):
    def __enter__(self):
        connect_params = {
            'creator': MySQLdb,
            'host': CommonConfig.database_host,
            'port': CommonConfig.database_port,
            'user': CommonConfig.database_user,
            'password': CommonConfig.database_password,
            'db': CommonConfig.database_name,
            'charset': 'utf8',
            'cursorclass': MySQLdb.cursors.DictCursor,
            'maxconnections': 50
        }

        # 在进入的时候自动获取连接和cursor
        # 从连接池获取数据库连接
        g_pool_connection = MysqlPoolInstance.get_storage_instance(connect_params)
        conn = g_pool_connection.get_conn()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        conn.autocommit = False

        self._conn = conn
        self._cursor = cursor
        return self

    def __exit__(self, *exc_info):
        # 提交事务
        self._conn.commit()
        # 在退出的时候自动关闭连接和cursor
        self._cursor.close()
        self._conn.close()

    def do_action(self, sql):
        self.cursor.execute(sql)

    @property
    def cursor(self):
        return self._cursor

