class MiddlewareBase:
    """中间件基类"""

    def __init__(self, handler, **kwargs):
        self.handler = handler
        self.kwargs = kwargs

    def __call__(self, request):
        """中间件调用函数"""
        return self.process_request(request)

    def process_request(self, request):
        """处理请求"""
        raise NotImplementedError()

    @classmethod
    def generate_nui_name(cls, **kwargs):
        """根据类名和kwargs生成对象名称"""
        return f"{cls.__name__}_{'_'.join(f'{k}_{v}' for k, v in kwargs.items())}"
