
# 自定义业务异常
class VException(Exception):
    def __init__(self, code, msg):
        super(Exception, self).__init__()
        self.code = code
        self.msg = msg

    def get_code(self):
        return self.code

    def get_msg(self):
        return self.msg



# 特殊异常抛出
class KException(Exception):
    def __init__(self):
        super(Exception, self).__init__()



# 权限异常
class PermissException(Exception):
    def __init__(self, code, msg, data=None):
        self.code = code
        self.msg = msg
        self.data = data

    def get_code(self):
        return self.code

    def get_msg(self):
        return self.msg

    def get_data(self):
        return self.data