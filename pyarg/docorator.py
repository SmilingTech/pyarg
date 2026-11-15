from __future__ import annotations

import inspect
from typing import Any, Callable, overload

from pyarg.parser import PyArg

# Types.
SetupFunction = Callable[[PyArg], None]


# Functions.
@overload
def pyarg(func: SetupFunction, /) -> PyArg: ...
@overload
def pyarg(
    *, name: str | None = None, description: str | None = None, **kwargs: Any
) -> Callable[[SetupFunction], PyArg]: ...
def pyarg(
    func: SetupFunction | None = None, /, *, name: str | None = None, description: str | None = None, **kwargs: Any
) -> PyArg | Callable[[SetupFunction], PyArg]:
    """Create a **PyArg** parser from a function that defines its arguments."""

    def decorator(func: SetupFunction) -> PyArg:
        class_name: str = "".join([sub_name.title() for sub_name in func.__name__.split("_")])
        parser_class: type[PyArg] = type(
            class_name,
            (PyArg,),
            {"setup_arguments": lambda self: func(self), "__doc__": func.__doc__, "__module__": func.__module__},
        )
        return parser_class(
            name=name or func.__name__.replace("_", " ").title(),
            description=description or inspect.getdoc(object=func),
            **kwargs,
        )

    return decorator(func=func) if func else decorator
