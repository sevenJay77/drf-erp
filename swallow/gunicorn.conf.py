import os
from config.config import CommonConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

bind = "0.0.0.0:{}".format(CommonConfig.bind_port)
workers = CommonConfig.workers_number
threads = CommonConfig.threads_number

errorlog = os.path.join(LOG_DIR, 'gunicorn.log')
worker_class = "gevent"
forworded_allow_ips = '*'
worker_connections = 2000
timeout = 60
keepalive = 30
limit_request_line = 4094
limit_request_fields = 1000
limit_request_field_size = 8190
max_requests = 1000
max_requests_jitter = 50
reload = True