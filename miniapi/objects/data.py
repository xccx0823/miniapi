import typing as t


class _Know:
    """不明确的值"""


_know = _Know()


class DataObjects:
    """数据操作"""

    @staticmethod
    def o_get(data: t.List[dict], column: str, default: t.Any = None, ignore: bool = False) -> list:
        """获取字典或其他类型的对象的指定字段的值

        :param data: 数据
        :param column: 字段
        :param default: 默认值
        :param ignore: 没有取到对应的值的时候是否跳过本次获取，不跳过会使用默认值填充

        >>> from miniapi import objects
        >>>
        >>> example_data = [{'a': 1, 'b': 2, 'c': 3}, ...]
        >>> result = objects.o_get(example_data, 'a')
        >>> # result = [1, ...]
        """
        lis = []
        for row in data:
            value = row.get(column, _know)
            if isinstance(value, _Know):
                if ignore:
                    continue
                value = default

            lis.append(value)
        return lis

    @staticmethod
    def o_drop(data: t.List[dict], columns: list):
        """删除列表嵌套字典中的指定的多个字段

        :param data: 数据
        :param columns: 字段列表

        >>> from miniapi import objects
        >>>
        >>> example_data = [{'a': 1, 'b': 2, 'c': 3}, ...]
        >>> example_data = objects.o_drop(example_data, ['a'])
        >>> # example_data = [{'b': 2, 'c': 3}, ...]
        """
        drop_data = []
        for row in data:
            for column in columns:
                row.pop(column, None)
            drop_data.append(row)
        return drop_data

    @staticmethod
    def o_index(data: t.List[list], index: int = 0, default: t.Any = None, ignore: bool = False) -> list:
        """获取列表嵌套字典和可以索引取值的对象里面的指定索引位置的值

        :param data: 数据
        :param index: 索引
        :param default: 默认值
        :param ignore: 没有取到对应的值的时候是否跳过本次获取，不跳过会使用默认值填充

        >>> from miniapi import objects
        >>>
        >>> example_data = [[1, 2, 3], ...]
        >>> result = objects.o_index(example_data, 1)
        >>> # result = [2, ...]
        """
        values = []
        for row in data:
            if len(row) == 0:
                if ignore:
                    continue
                value = default
            else:
                value = row[index]
            values.append(value)
        return values

    @staticmethod
    def checkout(rule, many=False):
        """检查请求参数

        :param rule: 参数规则
        :param many: 校验请求的参数是否是列表
        """

        def wrapper(func):
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            return inner

        return wrapper

    @staticmethod
    def serialization(serialize, many=False):
        """序列化返回结果

        :param serialize: 序列化类
        :param many: 返回的结果是否是列表
        """

        def wrapper(func):
            def inner(*args, **kwargs):
                return func(*args, **kwargs)

            return inner

        return wrapper
