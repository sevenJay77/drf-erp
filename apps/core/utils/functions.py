import string
import time
import json
import datetime
import urllib.request
import re
from PIL import Image
import random
import uuid


#######################################
# 生成随机验证码
######################################
def generate_verify_code(times):
    code = ""
    for i in range(times):
        current = random.randint(0, 9)
        code += str(current)
    return code


#######################################
# 生成随机密码
######################################
def generate_password(level='1'):
    """
    :param int level:       level(密码复杂度)
    :return:
    """

    # 选择密码复杂度
    if level == '2':
        parents = ''.join((string.ascii_letters, string.digits))
    elif level == '3':
        parents = ''.join((string.ascii_letters, string.digits, '!@#$%^&*'))
    else:
        parents = string.digits

    pwd = ''
    for i in range(6):
        pwd = ''.join((pwd, random.choice(parents)))

    return pwd


#######################################
# 手机号校验
######################################
def match_mobile(phone_number):
    ret = re.match(r"^1[345678]\d{9}$", phone_number)
    if ret:
        return True

    return False



#######################################
# 邮箱校验
######################################
def match_email(email_address):
    ret = re.match(r"[^@]+@[^@]+\.[^@]+", email_address)
    if ret:
        return True

    return False




#######################################
# 校验日期字符串
######################################
def match_date(str_date):
    '''判断是否是一个有效的日期字符串'''
    try:
        time.strptime(str_date, "%Y-%m-%d %H:%M:%S")
    except Exception:
        raise Exception('输入参数错误')

    return True

#######################################
# 版本号校验
######################################
def match_edition(version_number):
    ret = re.match(r"^\d+\.\d+\.\d+$", version_number)
    if ret:
        return True

    return False


#######################################
# 车牌号校验
######################################
def match_plate(number):
    rule  = '^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1}$'

    ret = re.findall(rule, number)
    if len(ret) == 0:
        return False
    return True


#######################################
# 获取访问ip地址
######################################
def get_ip_address(request):
    # 判断是否使用代理
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 使用代理获取真实的ip
            ip = x_forwarded_for.split(',')[0]
        else:
            # 未使用代理获取IP
            ip = request.META.get('REMOTE_ADDR')
    except:
        return ''

    return ip


#######################################
# 生成token
######################################
def generate_token():
    code_key = uuid.uuid1()
    code_key = str(code_key).replace('-', '')
    return code_key



#######################################
# 生成随机数
######################################
def generate_random_key(length):
    str_list = random.sample(string.digits, length)
    random_str = ''.join(str_list)
    return random_str


#######################################
# 生成编号
######################################
def generate_key():
    base_code = datetime.datetime.now().strftime('%y%m%d%H%M%S')
    str_list = random.sample(string.digits, 7)
    random_str = ''.join(str_list)
    code_key = base_code + random_str
    return code_key


#############################################
# 过滤输入字符串中的空格
# True 过滤所有空格
# False 连续空格转换为一个空格， HTML显示
############################################
def filter_space(search, clean=False):
    if clean:
        info = re.sub(' +', '', search)
    else:
        info = re.sub(' +', ' ', search)
    return info.strip()


#######################################
# 返回错误信息
######################################
def error_400_info(error, message="错误"):
    r_message = ""
    try:
        # 根据错误类型格式
        if isinstance(error, dict):
            for key, value in error.items():
                r_message = value[0]
                break
        elif isinstance(error, list):
            r_message = error[0]
        else:
            r_message = message
    except:
        r_message = message

    return r_message



def error_info(error, message="错误"):
    r_message = ""
    try:
        for key, value in error.items():
            r_message = value
            break
    except:
        r_message = message

    return r_message



###########################################
# 获取到第二天凌晨的秒数
############################################
def get_rest_seconds():
    now = datetime.datetime.now()
    today_begin = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    tomorrow_begin = today_begin + datetime.timedelta(days=1)
    rest_seconds = (tomorrow_begin - now).seconds
    return rest_seconds


###########################################
#JSONEncoder不知道怎么去把这个数据转换成json字符串的时候，
#它就会调用default()函数，default()函数默认会抛出异常。
#所以，重写default()函数来处理datetime类型的数据。
###########################################
class JsonToDatetime(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H: %M: %S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


###########################################
# 格式化多项传值
###########################################
def format_multi_conditions(value):
    conditions = []
    multi_list = value.split(',')
    for val in multi_list:
        if val.strip() == '':
            continue
        conditions.append(val)
    conditions = list(set(conditions))
    return conditions


###########################################
# 下载图片  type  0不resize, 1 宽度  2 高度
###########################################
def down_picture(dir_path, url, type, value=0):
    pic_path = "{}/{}.jpg".format(dir_path, int(time.time() * 1000))
    urllib.request.urlretrieve(url, pic_path)

    im = Image.open(pic_path)
    mode = im.mode
    if mode not in ('L', 'RGB'):
        if mode == 'RGBA':
            # 透明图片需要加白色底
            alpha = im.split()[3]
            bgmask = alpha.point(lambda x: 255 - x)
            im = im.convert('RGB')
            # paste(color, box, mask)
            im.paste((255, 255, 255), None, bgmask)
        else:
            im = im.convert('RGB')

    size = (0, 0)
    # 获取宽高
    width, height = im.size
    region = im.crop()
    if type == 1:
        thumb = region.resize((value, int(value * height / width)), Image.ANTIALIAS)
        thumb.save(pic_path, quality=100)
        size = (value, int(value * height / width))

    elif type == 2:
        thumb = region.resize((int(value * width / height), value), Image.ANTIALIAS)
        thumb.save(pic_path, quality=100)
        size = ((int(value * width / height), value))

    return pic_path, size

