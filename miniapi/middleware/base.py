class MiddlewareBase:

    def before_request(self, request):
        """请求前处理"""
        pass

    def after_request(self, request, response):
        """请求后处理"""
        pass

    def uni_name(self):
        """获取中间件名称"""
        return self.__class__.__name__
