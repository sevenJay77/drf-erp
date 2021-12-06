from django.db import connection
import logging

logger = logging.getLogger("django")


'''
统计数据库的查询次数和时间
'''
def query_time():
    total_time = 0
    queries = connection.queries
    for query in queries:
        query_time = query['time']
        query_time = float(query_time)
        total_time += query_time
    count_info = {
        'count': len(queries),
        'time': total_time
    }
    logger.info(count_info)


