import json

from werkzeug.wrappers import Response as _Response


class Response(_Response):
    pass


def adaption_response(response):
    if isinstance(response, (list, dict)):
        return Response(json.dumps(response))
    elif isinstance(response, Response):
        return response
    elif isinstance(response, (str, int, float, bool)):
        return Response(str(response), 200)
    elif isinstance(response, tuple) and len(response) == 2:
        code, message = response
        return Response(str(message), code)
    else:
        return Response('Internal Server Error', 500)
