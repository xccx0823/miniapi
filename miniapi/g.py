import typing as t

from miniapi.config import _SetupConfig
from miniapi.objects import Objects

objects: t.Optional[Objects] = None
config: t.Optional[_SetupConfig] = None
app: t.Optional[t.Any] = None
