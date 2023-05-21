import sys
from typing import Callable, TypeVar

if sys.version_info >= (3, 10):
    from typing import ParamSpec, TypeAlias
else:
    from typing_extensions import ParamSpec, TypeAlias


P = ParamSpec("P")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)

WrappedFunction: TypeAlias = Callable[P, T]
