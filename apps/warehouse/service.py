import datetime
from core.utils.redis_client import RedisClientInstance
from warehouse.models import Warehouse, Product

def generate_warehouse_code(prefix):
    redis_client = RedisClientInstance.get_storage_instance()
    # 前缀 + {yyyyMMdd} + 自增4位序号
    cache_key = "serial_number:{}".format(prefix)
    # if day_code:
    #     cache_key += datetime.datetime.now().strftime('%Y%m%d')
    # 判断redis key是否存在
    cache_value = redis_client.get_by_name(cache_key)
    if not cache_value is None:
        increase = redis_client.increase_by(cache_key)
    else:
        # 获取已有数据
        if prefix == 'CK':
            last_record = Warehouse.objects.order_by('-id').first()
        else:
            last_record = Product.objects.order_by('-id').first()
        if not last_record or not last_record.code:
            increase = 1
        else:
            code = last_record.code
            increase = int(code[-4:]) + 1
        # 设置redis
        redis_client.single_set_string_expire_next_day(cache_key, increase)
    result = "{}{}".format(prefix, str(increase).zfill(4))
    return result