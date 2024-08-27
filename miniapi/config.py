import os
import typing as t

import yaml


class _SetupConfig:
    """初始化的配置管理"""

    SOCKET_CONFIG_KEY = 'socket'
    MIDDLEWARES_CONFIG_KEY = 'middlewares'
    FINAL_CONFIG_KEY = 'final'

    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 3323

    def __init__(self, root_path):
        # 全局配置
        self.config = self.read_app_yaml(root_path)

        # 全局常量
        # 全局常量的key以及其签到结构中的字典的key都会转化为大写
        final = self.recursively_capitalize_keys(self.config.get(self.FINAL_CONFIG_KEY))
        self.final = final

    def get_socket_info(self) -> t.Tuple[str, int]:
        """获取并校验启动信息配置"""
        conf = self.config.get(self.SOCKET_CONFIG_KEY, dict())
        host = conf.pop('host', self.DEFAULT_HOST)
        port = conf.pop('port', self.DEFAULT_PORT)
        return host, port

    def get_middleware(self) -> t.List[str]:
        """获取中间件配置"""
        return self.config.get(self.MIDDLEWARES_CONFIG_KEY, [])

    def get_final(self) -> dict:
        """定义全局配置常量"""
        return self.config.get(self.FINAL_CONFIG_KEY)

    @staticmethod
    def read_app_yaml(root_path):
        """读取app所需要的ini配置文件"""
        with open(os.path.join(root_path, 'application.yaml'), 'r') as file:
            data = yaml.safe_load(file)
        return data

    def recursively_capitalize_keys(self, input_data):
        """将传入数据中的字典的key转化为大写，不管嵌套多深"""
        if isinstance(input_data, dict):
            new_dict = {}
            for key, value in input_data.items():
                new_key = key.upper()
                new_value = self.recursively_capitalize_keys(value)
                new_dict[new_key] = new_value
            return new_dict
        elif isinstance(input_data, list):
            new_list = []
            for item in input_data:
                new_list.append(self.recursively_capitalize_keys(item))
            return new_list
        else:
            return input_data
