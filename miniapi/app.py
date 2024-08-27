import inspect
import os
import typing as t
from wsgiref.simple_server import make_server

import yaml

from miniapi.const import HTTP_METHODS
from miniapi.exc import HTTPException
from miniapi.middleware.base import MiddlewareBase
from miniapi.objects import Objects
from miniapi.request import Request
from miniapi.response import Response
from miniapi.route import HandlerMapper
from miniapi.status import HTTPStatus
from miniapi.utils import get_root_path, import_string

objects: t.Optional[Objects] = None


class _SetupConfigManager:
    """初始化的配置管理"""

    SOCKET_CONFIG_KEY = 'socket'
    PLUGINS_CONFIG_KEY = 'plugins'
    MIDDLEWARES_CONFIG_KEY = 'middlewares'
    FINAL_CONFIG_KEY = 'final'

    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 3323

    def __init__(self, root_path):
        # 全局配置
        self.config = self.read_app_yaml(root_path)

        # 全局常量
        # 全局常量的key以及其签到结构中的字典的key都会转化为大写
        final = self.recursively_capitalize_keys(self.config.get(self.FINAL_CONFIG_KEY))
        self.final = final

    def get_socket_info(self) -> t.Tuple[str, int]:
        """获取并校验启动信息配置"""
        config = self.config.get(self.SOCKET_CONFIG_KEY, dict())
        host = config.pop('host', self.DEFAULT_HOST)
        port = config.pop('port', self.DEFAULT_PORT)
        return host, port

    def get_middleware(self) -> t.List[str]:
        """获取中间件配置"""
        return self.config.get(self.MIDDLEWARES_CONFIG_KEY, [])

    def get_plugin(self) -> t.List[str]:
        """获取插件配置"""
        return self.config.get(self.PLUGINS_CONFIG_KEY, [])

    def get_final(self) -> dict:
        """定义全局配置常量"""
        return self.config.get(self.FINAL_CONFIG_KEY)

    @staticmethod
    def read_app_yaml(root_path):
        """读取app所需要的ini配置文件"""
        with open(os.path.join(root_path, 'application.yaml'), 'r') as file:
            data = yaml.safe_load(file)
        return data

    def recursively_capitalize_keys(self, input_data):
        """将传入数据中的字典的key转化为大写，不管嵌套多深"""
        if isinstance(input_data, dict):
            new_dict = {}
            for key, value in input_data.items():
                new_key = key.upper()
                new_value = self.recursively_capitalize_keys(value)
                new_dict[new_key] = new_value
            return new_dict
        elif isinstance(input_data, list):
            new_list = []
            for item in input_data:
                new_list.append(self.recursively_capitalize_keys(item))
            return new_list
        else:
            return input_data


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
        self.__config = _SetupConfigManager(root_path)

        # 插件和中间件的表现形式一样，不同的区别在于插件在配置文件中被义后时不会被中间件注册函数影响的，也就是固定会执行的，
        # 而中间件则可以根据接口的定义情况来决定是否执行。
        self.plugins_list: list = []
        self.middlewares_list: list = []

        # 自定义异常拦截函数列表
        self.error_blocking_funcs: list = []

        # 路由映射执行函数
        self.__handlers_mapper = HandlerMapper()

    def config(self):
        return self.__config.config

    def final(self):
        return self.__config.final

    def set_objects(self, objs_cls: t.Type[Objects] = None):
        """添加继承了Objects的类，用于额外添加功能"""
        global objects
        objects = objs_cls(self)
        self.objects = objects

    def _make_objects(self, objs_cls: t.Type[Objects] = None):
        global objects
        if objs_cls:
            objects = objs_cls(self)
        else:
            objects = Objects(self)
        return objects

    def run(self):
        host, port = self.__config.get_socket_info()
        with make_server(host, port, self) as server:
            print(f"Serving on {host}:{port}...")
            server.serve_forever()

    def wsgi_app(self, environ, start_response):
        """wsgi请求上下文"""
        request = Request(environ)
        try:
            response = self.dispatch_request(request)
        except Exception as e:

            # miniapi HTTPException异常拦截
            if isinstance(e, HTTPException):
                return Response(status=e.status)

            # 其他异常均以500异常返回
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

        return response(environ, start_response)

    def dispatch_request(self, request):
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
            if not issubclass(_m, MiddlewareBase):
                raise AssertionError(f'中间件类型错误,请继承MiddlewareBase类')
        for _m in forbidden:
            if not issubclass(_m, MiddlewareBase):
                raise AssertionError(f'中间件类型错误,请继承MiddlewareBase类')
        _middlewares = []
        for _m in self.middlewares_list + middlewares:
            if _m in forbidden:
                continue
            if _m in _middlewares:
                continue
            _middlewares.append(_m)

        self.__handlers_mapper.add(path, _methods, func, middlewares=middlewares)

    def middlewares(self, middleware):
        """注册全局中间件"""
        if isinstance(middleware, str):
            middleware = import_string(middleware)

        if not issubclass(middleware, MiddlewareBase):
            raise AssertionError(f'中间件类型错误,请继承MiddlewareBase类')

        self.middlewares_list.append(middleware)
