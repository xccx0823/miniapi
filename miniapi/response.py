import json
import mimetypes
import typing as t

from miniapi.status import HTTPStatus

try:
    import orjson
except ImportError:
    orjson = None


class Response:
    def __init__(self, body: t.Any = None, status=HTTPStatus.OK, headers=None, content_type='text/html'):
        self.body = body
        self.status = status
        self.headers = headers if headers is not None else []
        self.content_type = content_type
        self.headers.append(('Content-Type', self.content_type))

    def set_body(self, body):
        self.body = body

    def set_status(self, status):
        self.status = status

    def add_header(self, key, value):
        self.headers.append((key, value))

    def get_response(self):
        return {'status': self.status, 'headers': self.headers, 'body': self.body}


class FileStreamResponse(Response):
    def __init__(self, io: bytes, filename: str, status=HTTPStatus.OK, headers=None):
        headers = headers if headers is not None else []
        filetype, _ = mimetypes.guess_type(filename)
        filetype = filetype or 'application/octet-stream'
        headers.append(('Content-Type', filetype))
        headers.append(('Content-Disposition', f'attachment; filename="{filename}"'))
        super().__init__(body=io, status=status, headers=headers, content_type=filetype)


class JsonResponse(Response):
    def __init__(self, data, status=HTTPStatus.OK, headers=None, **json_kwargs):
        body = json.dumps(data, **json_kwargs)
        content_type = 'application/json'
        headers = headers if headers is not None else []
        headers.append(('Content-Type', content_type))
        super().__init__(body=body, status=status, headers=headers, content_type=content_type)


class OrJsonResponse(Response):
    def __init__(self, data, status=HTTPStatus.OK, headers=None, **orjson_kwargs):
        if orjson is None:
            raise ImportError('orjson未安装，请安装它以使用OrJsonResponse.')
        body = orjson.dumps(data, **orjson_kwargs)
        content_type = 'application/json'
        headers = headers if headers is not None else []
        headers.append(('Content-Type', content_type))
        super().__init__(body=body, status=status, headers=headers, content_type=content_type)
