import typing as t


class Route:

    def __init__(self, prefix='/'):
        self.prefix = prefix

    def get_url(self):
        pass


class HandlerMapper:

    def __init__(self):
        self.__mapper: dict = {}
        self._path_mapper: dict = {}

    def get(self, path, method):
        return self.__mapper[self._path_mapper[path]][method]

    def add(self, path, methods, handler, middlewares):
        endpoint = handler.__name__
        for method in methods:
            path_exist, method_exist = self.exists(endpoint, method)
            if path_exist and method_exist:
                raise AssertionError(f"{method} {path} 已经注册过了")
            self._path_mapper[path] = endpoint
            self.__mapper[endpoint] = dict()
            self.__mapper[endpoint][method] = (handler, middlewares)

    def exists(self, path, method) -> t.Tuple[bool, bool]:
        if path in self._path_mapper:
            path_exist = True
            if method in self.__mapper[self._path_mapper[path]]:
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
