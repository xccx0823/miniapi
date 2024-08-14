import importlib.util
import os
import sys
import typing as t


def import_string(import_name: str) -> t.Any:
    """基于字符串导入对象"""
    import_name = import_name.replace(":", ".")
    try:
        __import__(import_name)
    except ImportError:
        if "." not in import_name:
            raise
    else:
        return sys.modules[import_name]

    module_name, obj_name = import_name.rsplit(".", 1)
    module = __import__(module_name, globals(), locals(), [obj_name])
    try:
        return getattr(module, obj_name)
    except AttributeError as e:
        raise ImportError(e) from None


def get_root_path(import_name: str) -> str:
    """查找包的根路径，或者包含模块。如果找不到，则返回当前工作目录中。"""
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, "__file__") and mod.__file__ is not None:
        return os.path.dirname(os.path.abspath(mod.__file__))
    try:
        spec = importlib.util.find_spec(import_name)

        if spec is None:
            raise ValueError
    except (ImportError, ValueError):
        loader = None
    else:
        loader = spec.loader
    if loader is None:
        return os.getcwd()
    if hasattr(loader, "get_filename"):
        filepath = loader.get_filename(import_name)
    else:
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, "__file__", None)
        if filepath is None:
            raise RuntimeError(
                f"无法为所提供的模块找到根路径 {import_name!r}。"
            )
    return os.path.dirname(os.path.abspath(filepath))
