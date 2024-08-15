class MethodView:
    """视图接口"""

    middlewares: list = None

    def __init__(self):
        self.location: str

    def as_views(self):
        return self
