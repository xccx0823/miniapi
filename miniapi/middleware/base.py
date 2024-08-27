class MiddlewareBase:
    """中间件基类"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @staticmethod
    def before_request(request):
        """在请求前执行的钩子函数"""
        return request

    @staticmethod
    def after_request(response):
        """在请求后执行的钩子函数"""
        return response

    def generate_object_nui_name(self):
        """根据类名和kwargs生成对象名称"""
        return f"{self.__class__.__name__}_{'_'.join([str(k) + '_' + str(v) for k, v in self.kwargs.items()])}"
