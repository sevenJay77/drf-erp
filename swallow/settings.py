"""
Django settings for swallow project.
"""
######################################
# 兼容其他环境
######################################
import os
import sys
import datetime
from config.config import CommonConfig


######################################
# 配置相关目录
######################################
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


######################################
# 安全配置
#####################################
SECRET_KEY = '1+-&ds0jx%6$#2*7clbmfq)i=aqwo4w&1ipx9osqhjz^@lqse3'

DEBUG = CommonConfig.debug_mode

ALLOWED_HOSTS = ['*']

ATOMIC_REQUESTS = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

######################################
# 模块配置
######################################
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_yasg',
    # 自定义模块
    'permcontrol',
    'app_edition',
    'operate_record',
    'audit',
    'common',
    'warehouse',

]


######################################
# 跨域配置
######################################
# 增加忽略
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = CommonConfig.origin_list_tuple
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)

CORS_ALLOW_HEADERS = (
    'accept',
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',
    'Access-Token',
    'Cache-Control'
)

######################################
# 中间件配置
######################################
MIDDLEWARE = [
    # 安全设置，比如XSS脚本过滤
    'django.middleware.security.SecurityMiddleware',
    # URL转义
    'django.middleware.common.CommonMiddleware',
    # 跨域请求
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 防止欺骗点击
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

######################################
# 模板配置
######################################
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'swallow.wsgi.application'
ASGI_APPLICATION = 'swallow.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'apps.core.framework.redis_channels.CommonRedisChannelLayer',
        'CONFIG': {
            "hosts": ["redis://{}@{}:{}/{}".format(CommonConfig.redis_password,
                                                   CommonConfig.redis_host,
                                                   CommonConfig.redis_port,
                                                   CommonConfig.redis_position_db)],
            "group_expiry": 3600
        },
    },
}
######################################
# 数据库配置
######################################
DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
        'ENGINE': 'core.mysql_engine',  # 数据库引擎
        'NAME': CommonConfig.database_name,  # 你要存储数据的库名，事先要创建
        'USER': CommonConfig.database_user,  # 数据库用户名
        'PASSWORD': CommonConfig.database_password,  # 密码
        'HOST': CommonConfig.database_host,  # 主机
        'PORT': CommonConfig.database_port,  # 数据库使用的端口
        'CONN_MAX_AGE': None,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'maxconnections': 500,
        },
        'STORAGE_ENGINE': 'INNODB',
        'ATOMIC_REQUESTS': True,
    }
}


######################################
# 路由配置
######################################
ROOT_URLCONF = 'swallow.urls'


######################################
# 用户验证配置
######################################
AUTH_USER_MODEL = "permcontrol.User"


######################################
# 时间配置
######################################
LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


######################################
# REST FRAMEWORK配置
######################################
REST_FRAMEWORK = {
    # API渲染
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    # 分页
    'DEFAULT_PAGINATION_CLASS': 'apps.core.framework.pagination.StandardResultsSetPagination',
    # 登录
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.middleware.auth.CommonAuthentication'
    ],
    # 权限
    'DEFAULT_PERMISSION_CLASSES': (
        'apps.core.middleware.permissions.CustomPermissions',
    ),
    # 限流拦截
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.framework.throttle.UserRateThrottle',
    ],
    # 错误处理 展示在接口返回数据里
    'EXCEPTION_HANDLER': 'apps.core.framework.exception.custom_exception_handler',
}


######################################
# LOG配置
######################################

LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
   try:
       os.makedirs(LOG_DIR)
   except:
       pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'main_formatter': {
            'format': '%(asctime)s [%(process)d] [%(filename)s:%(funcName)s:%(lineno)d] [%(levelname)s]- %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter',
            'filters': ['require_debug_true'],
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'manager.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': CommonConfig.log_max_counts,
            'formatter': 'main_formatter',
            'encoding': 'utf-8',

        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': CommonConfig.log_max_counts,
            'formatter': 'main_formatter',
            'encoding': 'utf-8',
        },

    },
    'loggers': {
        'django': {
            'handlers': ['console', 'debug_file', 'error'],
            'level': "INFO",
            'propagate': True,
        },
        "gunicorn.access": {
            "handlers": ["debug_file"],
            "level": "INFO",
            "propagate": True,
        }
    },
}



######################################
# SWAGGER配置
######################################
SWAGGER_SETTINGS = {
    'PERSIST_AUTH': True,
    'REFETCH_SCHEMA_WITH_AUTH': False,
    'REFETCH_SCHEMA_ON_LOGOUT': False,
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Access-Token',
            'in': 'header'
        },
    }

}
