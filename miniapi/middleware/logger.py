import logging
import time
from datetime import datetime

from miniapi.middleware.base import MiddlewareBase
from miniapi.status import HTTPStatus


class LoggerMiddleware(MiddlewareBase):
    """miniapi提供的简易日志记录中间件，直接使用打印到终端"""

    def __init__(self, handler, **kwargs):
        super().__init__(handler)
        logger_name = kwargs.get('logger_name', 'miniapi')
        log = logging.getLogger(logger_name)
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
        self.logger = log

    def process_request(self, request):
        start = time.time()
        response = self.handler(request)
        end = time.time()

        if response.status.startswith('2'):
            fg_color = 30
            bg_color = 42
        elif response.status.startswith('3'):
            fg_color = 31
            bg_color = 41
        elif response.status.startswith('4'):
            fg_color = 33
            bg_color = 43
        elif response.status.startswith('5'):
            fg_color = 31
            bg_color = 41
        else:
            fg_color = 37
            bg_color = 47

        self.logger.info(
            f"{self.print_with_colors(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ', 30, 46)}"
            f"{self.print_with_colors(' ' + request.method + '::', fg_color, bg_color)}"
            f"{self.print_with_colors(request.path + ' ', fg_color, bg_color)}"
            f"{self.print_with_colors(response.status + ' ' + str(round(end - start, 3)) + 's ', fg_color, bg_color)}"
        )
        return response

    @staticmethod
    def print_with_colors(text, fg_color, bg_color):
        return f"\033[{fg_color};{bg_color}m{text}\033[0m"
