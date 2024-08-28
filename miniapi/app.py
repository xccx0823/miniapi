import inspect
import traceback
import typing as t
from wsgiref.simple_server import make_server

from miniapi import g
from miniapi.config import _SetupConfig
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

HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']


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

        # 初始化application.yaml配置
        self._config = self.init_config(root_path)

        # 全局中间件列表
        # middleware_mapper: 全局中间件映射表 {中间件类名: 中间件对象}
        # middleware_forbidden_mapper: 禁用全局中间件映射表 {请求方法 + 请求路径: 中间件类名列表}
        # middleware_partial_mapper: 局部中间件映射表 {请求方法 + 请求路径: 中间件对象列表}
        self.middleware_mapper: dict = {}
        self.middleware_forbidden_mapper: dict = {}
        self.middleware_partial_mapper: dict = {}
        self._load_config_middlewares()

        # 自定义异常拦截函数列表
        self.error_blocking_funcs: list = []

        # 路由映射执行函数
        self._handlers_mapper = HandlerMapper()

        # 扩展
        self.extensions = {}

        # app挂在g对象上
        g.app = self

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
        try:
            with make_server(host, port, self, ThreadingWSGIServer, WSGIRequestHandler) as server:
                print(f"Serving on http://{host}:{port}")  # noqa
                server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()

    @staticmethod
    def adapt_response(func):

        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            if isinstance(response, str):
                return Response(body=response)
            elif isinstance(response, bytes):
                return Response(body=response)
            elif isinstance(response, dict):
                return JsonResponse(response)
            elif isinstance(response, Response):
                return response
            else:
                raise ValueError(f"返回值类型错误,请返回str,bytes,dict,Response类型,当前返回值类型为{type(response)}")

        return wrapper

    def wsgi_app(self, environ, start_response):
        """wsgi请求上下文"""
        return self.dispatch_request(environ, start_response)

    def dispatch_request(self, environ, start_response):
        """请求处理"""
        request = Request(environ)

        try:
            request_key = f'{request.method}:{request.path}'
            forbidden_middleware_names = self.middleware_forbidden_mapper.get(request_key, [])

            # 全局中间件
            for name, middleware_obj in self.middleware_mapper.items():
                if name in forbidden_middleware_names:
                    continue
                request = middleware_obj.before_request(request)

            # 局部中间件
            partial_middleware_objs = self.middleware_partial_mapper.get(request_key, [])
            for middleware_obj in partial_middleware_objs:
                request = middleware_obj.before_request(request)

            try:
                response = self.context(request)
            except Exception as e:
                # miniapi HTTPException异常拦截
                if isinstance(e, HTTPException):
                    response = Response('', e.status)
                else:
                    # 其他异常均以500异常返回
                    # 打印堆栈信息
                    traceback.print_exc()
                    response = Response('', HTTPStatus.INTERNAL_SERVER_ERROR)

            for middleware_obj in reversed(partial_middleware_objs):
                response = middleware_obj.after_request(request, response)

            for name, middleware_obj in self.middleware_mapper.items():
                if name in forbidden_middleware_names:
                    continue
                response = middleware_obj.after_request(request, response)

        except Exception as e:

            # miniapi HTTPException异常拦截
            if isinstance(e, HTTPException):
                response = Response('', e.status)
            else:
                # 其他异常均以500异常返回
                # 打印堆栈信息
                traceback.print_exc()
                response = Response('', HTTPStatus.INTERNAL_SERVER_ERROR)

        start_response(response.status, response.headers)
        if isinstance(response.body, str):
            return [response.body.encode('utf-8')]
        elif isinstance(response.body, bytes):
            return [response.body]
        else:
            return [response.body]

    def context(self, request: Request) -> Response:
        # 404异常处理
        method_handlers = self._handlers_mapper.get_method_handlers(request.path)
        if not method_handlers:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        # 405异常处理
        handler = method_handlers.get(request.method, None)
        if not handler:
            raise HTTPException(HTTPStatus.METHOD_NOT_ALLOWED)

        return handler(request)

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
            middlewares: t.Optional[t.List[t.Union[MiddlewareBase, str]]] = None,
            forbidden: t.Optional[t.List[t.Union[MiddlewareBase, str]]] = None):
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

        # 添加自适应返回结果
        func = self.adapt_response(func)

        # 禁用全局中间件
        forbidden_middleware_objs = self._parse_route_middlewares(forbidden, is_obj=False)

        # 局部中间件
        middleware_objs = self._parse_route_middlewares(middlewares)

        for method in _methods:
            key = f'{method}:{path}'
            self.middleware_forbidden_mapper[key] = forbidden_middleware_objs
            self.middleware_partial_mapper[key] = middleware_objs
            self._handlers_mapper.add(path, method, func)

    def _parse_route_middlewares(self, middlewares, is_obj=True):
        """检查路由注册的中间件"""
        middleware_objs = []
        if not middlewares:
            return middleware_objs
        for m in middlewares:
            if isinstance(m, str):
                m_obj = self.middleware_mapper.get(m)
                if not m_obj:
                    raise AssertionError(f'未注册中间件:{m}')
                middleware_obj = m_obj
            elif not isinstance(m, MiddlewareBase):
                raise AssertionError('中间件类型错误,请继承MiddlewareBase类')
            else:
                middleware_obj = m
            if is_obj:
                middleware_objs.append(middleware_obj)
            else:
                middleware_objs.append(middleware_obj.uni_name())
        return middleware_objs

    def add_middlewares(self, middleware: t.Union[MiddlewareBase, str]):
        """注册全局中间件"""
        if isinstance(middleware, str):
            middleware = import_string(middleware)()

        if not isinstance(middleware, MiddlewareBase):
            raise AssertionError('中间件类型错误,请继承MiddlewareBase类')

        self.middleware_mapper[middleware.uni_name()] = middleware

    def _load_config_middlewares(self):
        """加载配置文件中的中间件"""
        for middleware_config in self._config.get_middleware():  # type: dict
            name = middleware_config.get('name')
            if not name:
                raise ValueError('\n\napplication.yaml 中 middleware 配置项缺少 name 字段\n\n'
                                 '# 示例: \n'
                                 'middlewares:\n'
                                 '  - name: demo.middleware.DemoMiddleware\n'
                                 '    demo_param: "*"')
            self.add_middlewares(name)
