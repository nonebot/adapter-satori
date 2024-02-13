from typing import Literal, overload

from nonebot.compat import PYDANTIC_V2

__all__ = ("model_validator",)


if PYDANTIC_V2:
    from pydantic import model_validator as model_validator
else:
    from pydantic import root_validator

    @overload
    def model_validator(*, mode: Literal["before"]): ...

    @overload
    def model_validator(*, mode: Literal["after"]): ...

    def model_validator(*, mode: Literal["before", "after"]):
        if mode == "before":
            return root_validator(pre=True, allow_reuse=True)
        else:
            return root_validator(skip_on_failure=True, allow_reuse=True)
