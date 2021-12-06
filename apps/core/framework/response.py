from rest_framework.response import Response
import logging

logger = logging.getLogger("django")

class VResponse(Response):
    def __init__(self, code=200, detail='', url=''):
        data_info = {
            "detail": detail,
        }

        logger.error("[website error] url: {}, error msg: {}， code: {}".format(url, detail, code))
        super(VResponse, self).__init__(data=data_info, status=code)


class PermissResponse(Response):
    def __init__(self, code=200, detail='', data=None):
        data_info = {
            "detail": detail,
            "data": data
        }

        logger.error("[permission error] error msg: {}".format(detail))
        super(PermissResponse, self).__init__(data=data_info, status=code)

