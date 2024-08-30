import typing as t


class MethodView:
    """视图接口"""

    middlewares: t.Union[t.List, t.Tuple, t.Tuple[t.List, t.Tuple]] = None
    forbidden: t.Union[t.List, t.Tuple, t.Tuple[t.List, t.Tuple]] = None

    def __init__(self):
        self.location: str

    def as_views(self):
        return self
