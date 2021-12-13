import threading
import oss2
import time
import uuid
import re
import urllib.parse

from config.config import AliModuleConfig
from core.framework.v_exception import VException

import logging
logger = logging.getLogger("django")


# 阿里OSS平台
class AliOssClient():
    def __init__(self):
        logger.info(" ================= ali oss init =====================")
        auth = oss2.Auth(AliModuleConfig.access_key_id, AliModuleConfig.access_secret)
        self.bucket = oss2.Bucket(auth, AliModuleConfig.oss_endpoint, AliModuleConfig.oss_bucket)

    # 多类型文件上传
    def upload_multi_file(self, file, file_type_list, usage):
        # 获取后缀名
        file_name = file.name
        suffix = file_name.split(".")[-1]
        # 文件内容
        content_type = file.content_type
        file_type = None
        # 后缀名
        suffix_dict = {
            'image': ['JPG', 'jpg', 'png', 'bmp', 'jpeg'],
            'video': ['mp4', 'avi', 'flv', 'mkv', 'mpeg'],
            'document': ['pdf', 'doc', 'docx'],
            'apk': ['apk'],
            'wgt': ['wgt']
        }

        for i_type in file_type_list:
            if i_type not in suffix_dict:
                raise VException(500, '文件类型不支持')

            if suffix in suffix_dict[i_type]:
                file_type = i_type
                break

        if file_type is None:
            raise VException(500, '上传文件格式受限制')

        # 图片后缀
        if file_type == 'image':
            if not re.match(r"^image/+", content_type):
                raise VException(500, "必须上传图片文件")
            # 文件大小校验
            max_image_size = 1024 * 1024 * 10
            if file.size > max_image_size:
                raise VException(500, "图片最大10M")
        elif file_type == 'video':
            if not re.match(r"^video/+", content_type):
                raise VException(500, "必须上传视频文件")
            # 文件大小校验
            max_video_size = 1024 * 1024 * 100
            if file.size > max_video_size:
                raise VException(500, "视频最大100M")
        elif file_type == 'document':
            if not re.match(r"^application/+", content_type):
                raise VException(500, "必须上传文档")
            # 文件大小校验
            max_video_size = 1024 * 1024 * 100
            if file.size > max_video_size:
                raise VException(500, "视频最大100M")
        elif file_type == 'apk':
            if not re.match(r"^application/+", content_type):
                raise VException(500, "必须上传Android应用程序包")
            # 文件大小校验
            max_apk_size = 1024 * 1024 * 100
            if file.size > max_apk_size:
                raise VException(500, "程序包最大100M")
        elif file_type == 'wgt':
            if not re.match(r"^application/+", content_type):
                raise VException(500, "必须上传热更新包")
            # 文件大小校验
            max_apk_size = 1024 * 1024 * 100
            if file.size > max_apk_size:
                raise VException(500, "热更新包最大100M")
        else:
            raise VException(500, '上传文件格式受限制')

        # 上传文件
        file_url = self.oss_simple_upload(file, suffix, usage)
        return file_url, file_type

    # 简单上传
    def oss_simple_upload(self, file, suffix, usage):
        # oss目录
        oss_dir = "ql_uploads/{}".format(usage)
        # 文件名重写
        file_name = "{}_{}".format(time.strftime('%Y%m%d%H%M%S'), uuid.uuid4().hex[:6])
        tmp_name = "{}.{}".format(file_name, suffix)
        # 上传
        try:
            file_content = file.read()
            oss_file_url = "{}/{}".format(oss_dir, tmp_name)
            result = self.bucket.put_object(oss_file_url, file_content)
            oss_url = "{}/{}".format(AliModuleConfig.oss_domain, oss_file_url)
        except Exception as e:
            logger.error("oss file error {}".format(e))
            raise VException(500, '文件上传失败')
        if result.status not in [200, 201]:
            raise VException(500, '文件上传失败')
        file_url = result.resp.response.url
        if not file_url:
            raise VException(500, '文件上传失败')
        return oss_url


class AliOssClientInstance(object):
    # 线程锁
    _instance_lock = threading.Lock()

    def __init__(self, *args,**kwargs):
        pass

    @classmethod
    def get_storage_instance(cls):
        if not hasattr(AliOssClientInstance,'_instance'):
            with AliOssClientInstance._instance_lock:
                AliOssClientInstance._instance = AliOssClient()
        return AliOssClientInstance._instance
