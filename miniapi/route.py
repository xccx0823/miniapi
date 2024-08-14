class Route:

    def __init__(self, prefix='/'):
        self.prefix = prefix

    def get_url(self):
        pass


class HandlerMapper:

    def __init__(self):
        self.__mapper = {}

    def get(self, path, method, is_exist=False):
        if is_exist:
            return self.__mapper[path][method]
        path_exist, method_exist = self.exists(path, method)
        if path_exist and method_exist:
            return self.__mapper[path][method]
        return None

    def add(self, path, methods, handler):
        for method in methods:
            path_exist, method_exist = self.exists(path, method)
            if path_exist and method_exist:
                raise AssertionError(f"{method} {path} 已经注册过了")
            self.__mapper[path] = dict()
            self.__mapper[path][method] = handler

    def exists(self, path, method) -> (bool, bool):
        if path in self.__mapper:
            path_exist = True
            if method in self.__mapper[path]:
                method_exist = True
            else:
                method_exist = False
        else:
            path_exist = False
            method_exist = False
        return path_exist, method_exist

    def print(self):
        """展示注册过的请求的地址以及请求方式"""
