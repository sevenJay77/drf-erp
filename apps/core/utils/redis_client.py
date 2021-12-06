# -*- coding:utf-8 -*-
import redis
import logging
import threading
from config.config import CommonConfig
from core.framework.v_exception import KException
from apps.core.utils.functions import get_rest_seconds

log = logging.getLogger("django")

class RedisClient:
    def __init__(self, host, port, password, db=0, decode_responses=False):
        log.info(' ================= redis  init =====================')
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.decode_responses = decode_responses
        self.socket_timeout = 5
        self.socket_connect_timeout = 2
        self.max_connections = 100
        self.redis_client = None
        # 创建连接
        self.connect()


    def connect(self):
        try:
            log.info(' ================= redis  connect =====================')
            connect_params = {
                'host': self.host,
                'port': self.port,
                'password': self.password,
                'db': self.db,
                'decode_responses': self.decode_responses,
                'socket_timeout': self.socket_timeout,
                'socket_connect_timeout': self.socket_connect_timeout,
            }

            if self.password:
                connect_params['password'] = self.password

            pool = redis.ConnectionPool(max_connections=self.max_connections, **connect_params)

            self.redis_client = redis.Redis(connection_pool=pool)
            return True
        except:
            return False

    def ping_connect(self):
        try:
            self.redis_client.ping()
            # redis_info = self.redis_client.info()
            # connected_clients = redis_info['connected_clients']
            # log.error("connected_clients : {}".format(connected_clients))
        except Exception as e:
            log.info('========== redis  connect  error {}=============='.format(e))
            raise KException()


    # 获取Redis服务器的时间 UNIX时间戳 + 这一秒已经逝去的微秒数
    def get_time(self):
        self.ping_connect()

        try:
            return self.redis_client.time()
        except:
            log.error('{}  执行失败'.format('Redis get time'))
            raise KException()

    # 获取所有对象名称
    def get_all_keys(self, pattern='*'):
        self.ping_connect()
        try:
            return self.redis_client.keys(pattern=pattern)
        except:
            log.error('{}  执行失败'.format('Redis get all keys'))
            raise KException()


    # 随机获取一个Key
    def get_random_key(self):
        self.ping_connect()
        try:
            return self.redis_client.randomkey()
        except:
            log.error('{}  执行失败'.format('Redis get randomkey'))
            raise KException()

    # 设置Key在固定时间之后过期
    def set_key_expire_after(self, name, unit, time):
        self.ping_connect()
        try:
            if unit == "second":
                return self.redis_client.expire(name, time)
            elif unit == "millisecond":
                return self.redis_client.pexpire(name, time)

        except:
            log.error('{}  执行失败'.format('Redis set_key_expire_after'))
            raise KException()


    # 设置Key在到达固定时间之时过期
    def set_key_expire_at(self, name, unit, time):
        self.ping_connect()
        try:
            if unit == "second":
                return self.redis_client.expireat(name, time)
            elif unit == "millisecond":
                return self.redis_client.pexpireat(name, time)

        except:
            log.error('{}  执行失败'.format('Redis set_key_expire_at'))
            raise KException()


    # 重新命名对象
    def rename_key(self, old_name, new_name):
        self.ping_connect()
        try:
            return self.redis_client.rename(old_name, new_name)

        except:
            log.error('{}  执行失败'.format('Redis rename_key'))
            raise KException()


    # 新Key不存在的情况下重命名
    def rename_key_if_not_exists(self, old_name, new_name):
        self.ping_connect()
        try:
            return self.redis_client.renamenx(old_name, new_name)

        except:
            log.error('{}  执行失败'.format('Redis rename_key'))
            raise KException()


    # 设置对象为永久保存
    def persist(self, name):
        self.ping_connect()
        try:
            return self.redis_client.persist(name)

        except:
            log.error('{}  执行失败'.format('Redis persist'))
            raise KException()

    # 判断是否有某个名字的对象
    def exists(self, name):
        self.ping_connect()
        try:
            return self.redis_client.exists(name)

        except:
            log.error('{}  执行失败'.format('Redis exists'))
            raise KException()


    # 删除对象
    def delete_by_name(self, name):
        self.ping_connect()
        try:
            return self.redis_client.delete(name)

        except:
            log.error('{}  执行失败'.format('Redis delete_by_name'))
            raise KException()

    def get_by_name(self, name):
        self.ping_connect()
        try:
            return self.redis_client.get(name)
        except:
            log.error('{}  执行失败'.format('Redis get_by_name'))
            raise KException()

    # 删除指定数据库中的内容
    def flush_database(self):
        self.ping_connect()
        try:
            return self.redis_client.flushdb()

        except:
            log.error('{}  执行失败'.format('Redis flush_database'))
            raise KException()

    # 删除整个Redis中的内容
    def flush_all(self):
        self.ping_connect()
        try:
            return self.redis_client.flushall()
        except:
            log.error('{}  执行失败'.format('Redis flush_all'))
            raise KException()


    '''
    String
    '''

    # 单个添加字符串
    def single_set_string(self, name, value):
        self.ping_connect()
        try:
            return self.redis_client.set(name, value)

        except:
            log.error('{}  执行失败'.format('Redis single_set_string'))
            raise KException()


    # 批量添加字符串
    def multi_set_string(self, *args, **kwargs):
        self.ping_connect()
        try:
            return self.redis_client.mset(*args, **kwargs)

        except:
            log.error('{}  执行失败'.format('Redis multi_set_string'))
            raise KException()

    # 获取单个字符串
    def single_get_string(self, name):
        self.ping_connect()
        try:
            return self.redis_client.get(name)

        except:
            log.error('{}  执行失败'.format('Redis single_get_string'))
            raise KException()

    # 批量获取字符串
    def multi_get_string(self, keys):
        self.ping_connect()
        try:
            return self.redis_client.mget(keys)

        except:
            log.error('{}  执行失败'.format('Redis multi_get_string'))
            raise KException()

    # 设置字符串并设置Key过期时间
    def single_set_string_with_expire_time(self, key, unit, time, value):
        self.ping_connect()
        try:
            if unit == "second":
                return self.redis_client.setex(key, time, value)
            elif unit == "millisecond":
                return self.redis_client.psetex(key, time, value)
        except Exception as e:
            log.error('{}  执行失败 {}'.format('Redis single_set_string_with_expire_time', e))
            raise KException()

    # 并发设置字符串
    def singe_setnx_string(self, key, value, time=None):
        self.ping_connect()
        try:
            return self.redis_client.set(key, value, ex=time, nx=True)
        except:
            log.error('{}  执行失败'.format('Redis singe_setnx_string'))
            raise KException()

    # 将给定 name 的值设为 value ，并返回 name 的旧值(old value)
    def get_and_set_string(self, name, value):
        self.ping_connect()
        try:
            return self.redis_client.getset(name, value)

        except:
            log.error('{}  执行失败'.format('Redis get_and_set_string'))
            raise KException()

    # 获取指定区间的字符串
    def get_string_by_range(self, name, start, end):
        self.ping_connect()
        try:
            return self.redis_client.getrange(name, start, end)

        except:
            log.error('{}  执行失败'.format('Redis get_string_by_range'))
            raise KException()

    # 获取字符串的长度
    def get_string_length(self, name):
        self.ping_connect()
        try:
            return self.redis_client.strlen(name)

        except:
            log.error('{}  执行失败'.format('Redis get_string_length'))
            raise KException()

    # 将String中指定偏移量的字符串更换为指定字符串
    def set_string_by_range(self, name, offset, value):
        self.ping_connect()
        try:
            return self.redis_client.setrange(name, offset, value)

        except:
            log.error('{}  执行失败'.format('Redis set_string_by_range'))
            raise KException()

    # 添加字符串到尾部
    def append_to_string_tail(self, name, value):
        self.ping_connect()
        try:
            return self.redis_client.append(name, value)

        except:
            log.error('{}  执行失败'.format('Redis append_to_string_tail'))
            raise KException()


    # Key中存储的数字值按给定值增加
    def increase_by(self, name, type="int", increment=1):
        self.ping_connect()
        try:
            if type == "int":
                return self.redis_client.incrby(name, increment)
            elif type == "float":
                return self.redis_client.incrbyfloat(name, increment)

        except:
            log.error('{}  执行失败'.format('Redis increase_by'))
            raise KException()

    # Key中存储的数字值按给定值减少
    def decrease_by(self, name, decrement=1):
        self.ping_connect()
        try:
            return self.redis_client.decrby(name, decrement)

        except:
            log.error('{}  执行失败'.format('Redis decrease_by'))
            raise KException()


    '''
    List
    '''

    # 获取List中元素个数
    def len_of_list(self, name):
        self.ping_connect()
        try:
            return self.redis_client.llen(name)

        except:
            log.error('{}  执行失败'.format('Redis len_of_list'))
            raise KException()


    # 插入元素到List头部
    def insert_to_list_head(self, name, *values):
        self.ping_connect()

        try:
            return self.redis_client.lpush(name, *values)

        except:
            log.error('{}  执行失败'.format('Redis insert_to_list_head'))
            raise KException()


    # 插入元素到List尾部
    def insert_to_list_tail(self, name, *values):
        self.ping_connect()

        try:
            return self.redis_client.rpush(name, *values)

        except:
            log.error('{}  执行失败'.format('Redis insert_to_list_tail'))
            raise KException()

    # 从List头部获取一个元素并删除
    def get_and_delete_from_list_head(self, name):
        self.ping_connect()

        try:
            return self.redis_client.lpop(name)

        except:
            log.error('{}  name: {} 执行失败'.format('Redis get_and_delete_from_list_head', name))
            raise KException()


    # 从List尾部获取一个元素并删除
    def get_and_delete_from_list_tail(self, name):
        self.ping_connect()

        try:
            return self.redis_client.rpop(name)

        except:
            log.error('{}  执行失败'.format('Redis get_and_delete_from_list_tail'))
            raise KException()

    # 移出并获取列表的第一个元素， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止
    def block_and_pop_first_item_in_list(self, keys, timeout=1):
        self.ping_connect()

        try:
            return self.redis_client.blpop(keys, timeout=timeout)

        except:
            log.error('{}  执行失败'.format('Redis block_and_pop_first_item_in_list'))
            raise KException()


    # 移出并获取列表的最后一个元素， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止
    def block_and_pop_last_item_in_list(self, keys, timeout=1):
        self.ping_connect()

        try:
            return self.redis_client.brpop(keys, timeout=timeout)

        except:
            log.error('{}  执行失败'.format('Redis block_and_pop_last_item_in_list'))
            raise KException()


    # 从列表中弹出一个值，将弹出的元素插入到另外一个列表中并返回它， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止
    def block_pop_item_from_list_and_push_to_list(self, src, dst, timeout=1):
        self.ping_connect()

        try:
            return self.redis_client.brpoplpush(src, dst, timeout=timeout)

        except:
            log.error('{}  执行失败'.format('Redis block_pop_item_from_list_and_push_to_list'))
            raise KException()


    # 从列表中弹出一个值，将弹出的元素插入到另外一个列表中并返回它
    def pop_item_from_list_and_push_to_list(self, src, dst):
        self.ping_connect()

        try:
            return self.redis_client.rpoplpush(src, dst)

        except:
            log.error('{}  执行失败'.format('Redis pop_item_from_list_and_push_to_list'))
            raise KException()


    # 获取List中的元素
    def get_item_in_list_by_index(self, name, index):
        self.ping_connect()

        try:
            return self.redis_client.lindex(name, index)

        except:
            log.error('{}  执行失败'.format('Redis get_item_in_list_by_index'))
            raise KException()


    # 将一个值插入到已存在的列表头部
    def insert_item_to_the_head_of_existent_list(self, name, item):
        self.ping_connect()

        try:
            return self.redis_client.lpushx(name, item)

        except:
            log.error('{}  执行失败'.format('Redis insert_item_to_the_head_of_existent_list'))
            raise KException()


    # 将一个值插入到已存在的列表尾部
    def insert_item_to_the_tail_of_existent_list(self, name, item):
        self.ping_connect()

        try:
            return self.redis_client.rpushx(name, item)

        except:
            log.error('{}  执行失败'.format('Redis insert_item_to_the_tail_of_existent_list'))
            raise KException()


    # 获取List中指定区间的元素
    def get_items_in_list_by_range(self, name, start, stop):
        self.ping_connect()

        try:
            return self.redis_client.lrange(name, start, stop)

        except:
            log.error('{}  执行失败'.format('Redis get_items_in_list_by_range'))
            raise KException()

    # 删除List中的元素
    def delete_item_in_list(self, name, count, value):
        """
        Remove the first ``count`` occurrences of elements equal to ``value``
        from the list stored at ``name``.

        The count argument influences the operation in the following ways:
           count > 0: Remove elements equal to value moving from head to tail.
           count < 0: Remove elements equal to value moving from tail to head.
           count = 0: Remove all elements equal to value.
        """
        self.ping_connect()

        try:
            return self.redis_client.lrem(name, count, value)

        except:
            log.error('{}  执行失败'.format('Redis delete_item_in_list'))
            raise KException()


    # 根据索引设置List中的元素
    def set_item_in_list_by_index(self, name, index):
        self.ping_connect()

        try:
            return self.redis_client.lset(name, index)

        except:
            log.error('{}  执行失败'.format('Redis set_item_in_list_by_index'))
            raise KException()

    #  保留List中指定区间元素
    def trim_items_in_list_by_range(self, name, start, end):
        self.ping_connect()

        try:
            return self.redis_client.ltrim(name, start, end)

        except:
            log.error('{}  执行失败'.format('Redis trim_items_in_list_by_range'))
            raise KException()

    # 设置字符串并设置Key隔天失效
    def single_set_string_expire_next_day(self, key, value):
        self.ping_connect()
        try:
            time = get_rest_seconds()
            self.redis_client.setex(key, time, value)
        except:
            log.error('{}  执行失败'.format('Redis single_set_string_expire_next_day'))
            raise KException()

    # 发布数据
    def publish(self, channel, message):
        self.ping_connect()

        try:
            return self.redis_client.publish(channel, message)

        except:
            log.error('{}  执行失败'.format('Redis publish'))
            raise KException()


    # 订阅
    def pubsub(self):
        self.ping_connect()
        try:
            return self.redis_client.pubsub()
        except:
            log.error('{}  执行失败'.format('Redis pubsub'))
            raise KException()



class RedisClientInstance(object):
    # 线程锁
    _instance_lock = threading.Lock()

    def __init__(self, *args,**kwargs):
        pass

    @classmethod
    def get_storage_instance(cls):
        if not hasattr(RedisClientInstance,'_instance'):
            with RedisClientInstance._instance_lock:
                RedisClientInstance._instance = RedisClient(host=CommonConfig.redis_host,
                                                            port=CommonConfig.redis_port,
                                                            password=CommonConfig.redis_password,
                                                            db=CommonConfig.redis_position_db)
            log.info('================= redis client instance  =====================')
        return RedisClientInstance._instance
