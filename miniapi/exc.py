from miniapi.status import HTTPStatus


class HTTPException(Exception):
    """HTTP请求异常基类"""

    def __init__(self, status: HTTPStatus):
        super().__init__(status)
        if status not in HTTPStatus.__dict__.values():
            raise KeyError(f'非法的HTTP状态码:{status}')
        self.status = status

    def __str__(self):
        return f'HTTPException: {self.status})'
