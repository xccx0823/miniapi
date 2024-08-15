import os
import typing as t

import yaml
from werkzeug import run_simple

from miniapi.const import HTTP_METHODS
from miniapi.exc import HTTPException
from miniapi.objects import Objects
from miniapi.request import Request
from miniapi.response import Response, adaption_response
from miniapi.route import HandlerMapper
from miniapi.utils import get_root_path

objects: t.Optional[Objects] = None


class _RouteContext:
    """APP请求路由分发上下文"""

    def __init__(self):
        # 注册的中间件列表
        self.middlewares: list = []

        # 自定义异常拦截函数列表
        self.error_blocking_funcs: list = []

        # 路由映射执行函数
        self.__handlers_mapper = HandlerMapper()

    def wsgi_app(self, environ, start_response):
        """wsgi请求上下文"""
        request = Request(environ)
        try:
            response = self.dispatch_request(request)
        except Exception as e:

            # miniapi HTTPException异常拦截
            if isinstance(e, HTTPException):
                return Response(e.message, e.code)(environ, start_response)

            # 其他异常均以500异常返回
            return Response('Internal Server Error', 500)(environ, start_response)

        return response(environ, start_response)

    def dispatch_request(self, request):
        path_exist, method_exist = self.__handlers_mapper.exists(request.path, request.method)
        if not path_exist:
            raise HTTPException(404)
        if not method_exist:
            raise HTTPException(405)
        handler = self.__handlers_mapper.get(request.path, request.method, is_exist=True)
        response = adaption_response(handler(request))
        return response

    def route(self, rule, methods: t.Optional[t.List[str]] = None):
        """注册普通函数的装饰器

        使用示例:
            >>> from miniapi import MiniApi
            >>>
            >>>
            >>> app = MiniApi(__name__)
            >>>
            >>> app.route('/index', methods=['GET'])
            >>> def index(request):
            >>>     ...
        """

        def decorator(func):
            self.add_url_rule(rule, methods, func)
            return func

        return decorator

    def get(self, rule):
        return self.route(rule, methods=['GET'])

    def post(self, rule):
        return self.route(rule, methods=['POST'])

    def put(self, rule):
        return self.route(rule, methods=['PUT'])

    def delete(self, rule):
        return self.route(rule, methods=['DELETE'])

    def patch(self, rule):
        return self.route(rule, methods=['PATCH'])

    def add_url_rule(self, path, methods: t.Optional[t.List[str]] = None, func=None):
        """函数的方式注册函数路由

        使用示例:
            >>> from miniapi import MiniApi
            >>>
            >>>
            >>> app = MiniApi(__name__)
            >>>
            >>> def index(request):
            >>>     ...
            >>>
            >>> app.add_url_rule('/index', index, methods=['GET'])
        """
        _methods = []
        for method in methods:
            method = method.upper()
            if method not in HTTP_METHODS:
                raise AssertionError(f'不支持的请求方式:{method},请在{HTTP_METHODS}中选择需要的请求方式.')
            _methods.append(method)
        self.__handlers_mapper.add(path, _methods, func)


class _SetupConfigManager:
    """初始化的配置管理"""

    SOCKET_CONFIG_KEY = 'socket'
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

    def get_socket_info(self) -> t.Tuple[str, int, dict]:
        """获取并校验启动信息配置"""
        config = self.config.get(self.SOCKET_CONFIG_KEY, dict())
        host = config.pop('host', self.DEFAULT_HOST)
        port = config.pop('port', self.DEFAULT_PORT)
        return host, port, config

    def get_middleware(self) -> t.List[str]:
        """获取中间件配置"""
        return self.config.get(self.MIDDLEWARES_CONFIG_KEY, [])

    def get_final(self) -> dict:
        """定义全局配置常量"""
        return self.config.get(self.FINAL_CONFIG_KEY)

    @staticmethod
    def read_app_yaml(root_path):
        """读取app所需要的ini配置文件"""
        with open(os.path.join(root_path, 'mini.yaml'), 'r') as file:
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


class MiniApi:
    """简易的api框架"""

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __init__(self, import_name: str, obj_cls: t.Type[Objects] = None, root_path: t.Optional[str] = None):
        # 生成root_path
        self.import_name = import_name
        if root_path is None:
            root_path = get_root_path(self.import_name)

        # Glight框架所有额外功能的装饰器以及函数方法
        self.objects = self._make_objects(obj_cls)

        # 请求上下文
        self.__context = _RouteContext()
        self.__config = _SetupConfigManager(root_path)

    def wsgi_app(self, environ, start_response):
        return self.__context.wsgi_app(environ, start_response)

    def config(self):
        return self.__config.config

    def final(self):
        return self.__config.final

    def route(self, rule, methods: t.Optional[t.List[str]] = None):
        return self.__context.route(rule, methods)

    def add_url_rule(self, path, methods: t.Optional[t.List[str]] = None, func=None):
        return self.__context.add_url_rule(path, methods, func)

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
        host, port, options = self.__config.get_socket_info()
        run_simple(host, port, self, **options)
