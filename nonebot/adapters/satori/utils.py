from functools import partial
from collections.abc import Awaitable
from typing_extensions import ParamSpec
from typing import Concatenate
from typing import TYPE_CHECKING, Generic, TypeVar, overload
from collections.abc import Callable

from nonebot.utils import logger_wrapper

if TYPE_CHECKING:
    from .bot import Bot

B = TypeVar("B", bound="Bot")
R = TypeVar("R")
P = ParamSpec("P")
log = logger_wrapper("Satori")


class API(Generic[B, P, R]):
    def __init__(self, func: Callable[Concatenate[B, P], Awaitable[R]]) -> None:
        self.func = func

    def __set_name__(self, owner: type[B], name: str) -> None:
        self.name = name

    @overload
    def __get__(self, obj: None, objtype: type[B]) -> "API[B, P, R]": ...

    @overload
    def __get__(self, obj: B, objtype: type[B] | None) -> Callable[P, Awaitable[R]]: ...

    def __get__(
        self, obj: B | None, objtype: type[B] | None = None
    ) -> "API[B, P, R] | Callable[P, Awaitable[R]]":
        if obj is None:
            return self

        return partial(obj.call_api, self.name)  # type: ignore

    async def __call__(self, inst: B, *args: P.args, **kwds: P.kwargs) -> R:
        return await self.func(inst, *args, **kwds)
