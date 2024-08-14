import typing as t

from werkzeug.http import HTTP_STATUS_CODES


class HTTPException(Exception):
    """HTTP请求异常基类"""

    def __init__(self, code: int, message: t.Optional[str] = None):
        super().__init__(message)
        if code not in HTTP_STATUS_CODES:
            raise KeyError(f'非法的HTTP状态码:{code}')
        self.code = code
        if message is None:
            message = HTTP_STATUS_CODES[code]
        self.message = message

    def __str__(self):
        return f'HTTPException:{self.message} (status code:{self.code})'


