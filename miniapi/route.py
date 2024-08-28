import inspect
import typing as t


class HandlerMapper:

    def __init__(self):
        self.__mapper: dict = {}
        self.endpoint_mapper: dict = {}

    def get_method_handlers(self, path):
        endpoint = self.endpoint_mapper.get(path)
        if not endpoint:
            return None
        method_handlers = self.__mapper[endpoint]
        return method_handlers

    def _get_handler_name(self, handler):
        if inspect.isfunction(handler):
            endpoint = handler.__name__
        else:
            endpoint = self._get_handler_name(handler.handler)
        return endpoint

    def add(self, path, method, handler):
        endpoint = self._get_handler_name(handler)
        path_exist, method_exist = self.exists(endpoint, method)
        if path_exist and method_exist:
            raise AssertionError(f"{method} {path} 已经注册过了")
        self.endpoint_mapper[path] = endpoint
        self.__mapper[endpoint] = dict()
        self.__mapper[endpoint][method] = handler

    def exists(self, path, method) -> t.Tuple[bool, bool]:
        if path in self.endpoint_mapper:
            path_exist = True
            if method in self.__mapper[self.endpoint_mapper[path]]:
                method_exist = True
            else:
                method_exist = False
        else:
            path_exist = False
            method_exist = False
        return path_exist, method_exist

    def print_mapper(self):
        """展示注册过的请求的地址以及请求方式"""
        for path, method_handlers in self.__mapper.items():
            print(f'| {path}')
            for method, handler in method_handlers.items():
                print(f'|: {method} {handler.__name__}')
