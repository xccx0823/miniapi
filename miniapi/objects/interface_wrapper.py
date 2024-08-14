class InterfaceWrapperObjects:
    """接口装饰器"""

    @staticmethod
    def middlewares(middles):
        """自定义中间件执行控制

        :param middles: 中间件列表
        """

        def wrapper(func):
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            return inner

        return wrapper

    @staticmethod
    def ratelimit(calls, period):
        """接口请求次数限流

        :param calls: 调用次数
        :param period: 时间区间
        """

        def wrapper(func):
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            return inner

        return wrapper
