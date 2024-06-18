from typing import Literal, Optional, overload

from nonebot.compat import PYDANTIC_V2

__all__ = ("model_validator", "field_validator")


if PYDANTIC_V2:
    from pydantic import field_validator as field_validator
    from pydantic import model_validator as model_validator
else:
    from pydantic import validator, root_validator

    @overload
    def field_validator(
        __field: str,
        *fields: str,
        mode: Literal["before"],
        check_fields: Optional[bool] = None,
    ): ...

    @overload
    def field_validator(
        __field: str,
        *fields: str,
        mode: Literal["after"],
        check_fields: Optional[bool] = None,
    ): ...

    def field_validator(
        __field: str,
        *fields: str,
        mode: Literal["before", "after"],
        check_fields: Optional[bool] = None,
    ):
        if mode == "before":
            return validator(__field, *fields, pre=True, check_fields=check_fields or True, allow_reuse=True)
        else:
            return validator(__field, *fields, check_fields=check_fields or True, allow_reuse=True)

    @overload
    def model_validator(*, mode: Literal["before"]): ...

    @overload
    def model_validator(*, mode: Literal["after"]): ...

    def model_validator(*, mode: Literal["before", "after"]):
        if mode == "before":
            return root_validator(pre=True, allow_reuse=True)
        else:
            return root_validator(skip_on_failure=True, allow_reuse=True)
