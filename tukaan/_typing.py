import sys
from typing import Any, Callable, Literal, TypeVar

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec, TypeAlias
else:
    from typing_extensions import Concatenate, ParamSpec, TypeAlias


P = ParamSpec("P")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)

WrappedFunction: TypeAlias = Callable[Concatenate[Any, P], T]
