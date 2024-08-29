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
