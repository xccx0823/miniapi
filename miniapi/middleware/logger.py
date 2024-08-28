import logging
import time
from datetime import datetime

from miniapi.middleware.base import MiddlewareBase

log = logging.getLogger('miniapi')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)


class LoggerMiddleware(MiddlewareBase):
    """miniapi提供的简易日志记录中间件，直接使用打印到终端"""

    def before_request(self, request):
        start = time.time()
        request.state['start_time'] = start
        return request

    def after_request(self, request, response):
        start = request.state['start_time']
        end = time.time()
        if response.status.startswith('2'):
            fg_color = 30
            bg_color = 42
        elif response.status.startswith('3'):
            fg_color = 30
            bg_color = 44
        elif response.status.startswith('4'):
            fg_color = 30
            bg_color = 43
        elif response.status.startswith('5'):
            fg_color = 30
            bg_color = 45
        else:
            fg_color = 30
            bg_color = 41

        if request.environ['QUERY_STRING']:
            path = ' ' + request.path + '?' + request.environ['QUERY_STRING'] + ' '
        else:
            path = ' ' + request.path + ' '

        log.info(
            f"{self.print_colors(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ', 30, 46)}"
            f"{self.print_colors(' ' + request.method + ' ', 30, 107)}"
            f"{self.print_colors(path, fg_color, bg_color)}"
            f"{self.print_colors(response.status + ' ' + str(round(end - start, 3)) + 's ', fg_color, bg_color)}"
        )
        return response

    @staticmethod
    def print_colors(text, fg_color, bg_color):
        return f"\033[{fg_color};{bg_color}m{text}\033[0m"
