import inspect
import typing as t
from wsgiref.simple_server import make_server

from miniapi import g
from miniapi.config import _SetupConfig
from miniapi.const import HTTP_METHODS
from miniapi.exc import HTTPException
from miniapi.httpserver.handler import WSGIRequestHandler
from miniapi.httpserver.server import ThreadingWSGIServer
from miniapi.middleware.base import MiddlewareBase
from miniapi.objects import Objects
from miniapi.request import Request
from miniapi.response import Response, JsonResponse
from miniapi.route import HandlerMapper
from miniapi.status import HTTPStatus
from miniapi.utils import get_root_path, import_string


class Application:
    """简易的api框架"""

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __init__(self, import_name: str, obj_cls: t.Type[Objects] = None, root_path: t.Optional[str] = None):
        # 生成root_path
        self.import_name = import_name
        if root_path is None:
            root_path = get_root_path(self.import_name)

        # miniapi框架所有额外功能的装饰器以及函数方法
        self.objects = self._make_objects(obj_cls)

        # 请求上下文
        self._config = self.init_config(root_path)

        # 全局中间件列表
        self.middlewares_list: list = []
        self._load_config_middlewares()

        # 自定义异常拦截函数列表
        self.error_blocking_funcs: list = []

        # 路由映射执行函数
        self.__handlers_mapper = HandlerMapper()

    def config(self):
        return self._config.config

    def final(self):
        return self._config.final

    def set_objects(self, objs_cls: t.Type[Objects] = None):
        """添加继承了Objects的类，用于额外添加功能"""
        _objs = objs_cls(self)
        g.objects = _objs
        self.objects = _objs

    @staticmethod
    def init_config(root_path: str) -> _SetupConfig:
        """初始化配置"""
        config = _SetupConfig(root_path)
        g.config = config
        return config

    def _make_objects(self, objs_cls: t.Type[Objects] = None):
        if objs_cls:
            _objs = objs_cls(self)
        else:
            _objs = Objects(self)
        g.objects = _objs
        return _objs

    def run(self):
        host, port = self._config.get_socket_info()
        with make_server(host, port, self, ThreadingWSGIServer, WSGIRequestHandler) as server:
            print(f"Serving on http://{host}:{port}")  # noqa
            server.serve_forever()

    @staticmethod
    def adapt_response(response):
        if isinstance(response, Response):
            return response
        elif isinstance(response, str):
            return Response(body=response)
        elif isinstance(response, (list, dict)):
            return JsonResponse(data=response)
        else:
            return Response(body=str(response))

    def wsgi_app(self, environ, start_response):
        """wsgi请求上下文"""
        request = Request(environ)
        try:
            response = self.dispatch_request(request)

            # 自适应返回结果
            response = self.adapt_response(response)

        except Exception as e:

            # miniapi HTTPException异常拦截
            if isinstance(e, HTTPException):
                start_response(e.status, [])
                return [b'']

            # 其他异常均以500异常返回
            # 打印堆栈信息
            import traceback
            traceback.print_exc()
            start_response(HTTPStatus.INTERNAL_SERVER_ERROR, [('Content-Type', 'text/plain')])
            return [b'']

        start_response(response.status, response.headers)
        if isinstance(response.body, str):
            return [response.body.encode('utf-8')]
        elif isinstance(response.body, bytes):
            return [response.body]
        else:
            return [response.body]

    def dispatch_request(self, request) -> Response:
        path_exist, method_exist = self.__handlers_mapper.exists(request.path, request.method)
        if not path_exist:
            raise HTTPException(HTTPStatus.NOT_FOUND)
        if not method_exist:
            raise HTTPException(HTTPStatus.METHOD_NOT_ALLOWED)
        handler, middlewares = self.__handlers_mapper.get(request.path, request.method)
        response = handler(request)
        return response

    def route(
            self,
            rule: str,
            methods: t.List[str],
            middlewares: t.Optional[list] = None,
            forbidden: t.Optional[list] = None):
        """注册普通函数的装饰器"""

        def decorator(func):
            self.add_url_rule(rule, func, methods, middlewares, forbidden)
            return func

        return decorator

    def get(self, rule: str, middlewares: t.Optional[list] = None, forbidden: t.Optional[list] = None):
        return self.route(rule, methods=['GET'], middlewares=middlewares, forbidden=forbidden)

    def post(self, rule: str, middlewares: t.Optional[list] = None, forbidden: t.Optional[list] = None):
        return self.route(rule, methods=['POST'], middlewares=middlewares, forbidden=forbidden)

    def put(self, rule: str, middlewares: t.Optional[list] = None, forbidden: t.Optional[list] = None):
        return self.route(rule, methods=['PUT'], middlewares=middlewares, forbidden=forbidden)

    def delete(self, rule: str, middlewares: t.Optional[list] = None, forbidden: t.Optional[list] = None):
        return self.route(rule, methods=['DELETE'], middlewares=middlewares, forbidden=forbidden)

    def patch(self, rule: str, middlewares: t.Optional[list] = None, forbidden: t.Optional[list] = None):
        return self.route(rule, methods=['PATCH'], middlewares=middlewares, forbidden=forbidden)

    def add_url_rule(
            self,
            path: str,
            func=None,
            methods: t.Optional[t.List[str]] = None,
            middlewares: t.Optional[list] = None,
            forbidden: t.Optional[list] = None):
        """函数的方式注册函数路由"""
        _methods = []
        for method in methods:
            method = method.upper()
            if method not in HTTP_METHODS:
                raise AssertionError(f'不支持的请求方式:{method},请在{HTTP_METHODS}中选择需要的请求方式.')
            _methods.append(method)

        # 检查func中是否包含request参数
        signature = inspect.signature(func)
        if 'request' not in signature.parameters:
            raise ValueError(f"函数 '{func.__name__}' 必须包含 'request' 参数.")

        # 检查中间件
        middlewares = middlewares or []
        forbidden = forbidden or []
        for _m in middlewares:
            if isinstance(_m, str):
                _m = import_string(_m)
            if not issubclass(_m, MiddlewareBase):
                raise AssertionError('中间件类型错误,请继承MiddlewareBase类')
        for _m in forbidden:
            if isinstance(_m, str):
                _m = import_string(_m)
            if not issubclass(_m, MiddlewareBase):
                raise AssertionError('中间件类型错误,请继承MiddlewareBase类')
        _middlewares = []
        for _m in self.middlewares_list + middlewares:
            if _m in forbidden:
                continue
            if _m in _middlewares:
                continue
            _middlewares.append(_m)

        self.__handlers_mapper.add(path, _methods, func, middlewares=middlewares)

    def middlewares(self, middleware, **params):
        """注册全局中间件"""
        if isinstance(middleware, str):
            middleware = import_string(middleware)

        if not issubclass(middleware, MiddlewareBase):
            raise AssertionError('中间件类型错误,请继承MiddlewareBase类')

        self.middlewares_list.append(middleware(**params))

    def _load_config_middlewares(self):
        """加载配置文件中的中间件"""
        for middleware_config in self._config.get_middleware():  # type: dict
            name = middleware_config.pop('name', None)
            if not name:
                raise ValueError('\n\napplication.yaml 中 middleware 配置项缺少 name 字段\n\n'
                                 '# 示例: \n'
                                 'middlewares:\n'
                                 '  - name: demo.middleware.DemoMiddleware\n'
                                 '    demo_param: "*"')
            self.middlewares(name, **middleware_config)
