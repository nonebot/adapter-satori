import json
from typing import Optional

from nonebot.drivers import Response
from nonebot.exception import AdapterException
from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class SatoriAdapterException(AdapterException):
    def __init__(self):
        super().__init__("satori")


class ActionFailed(BaseActionFailed, SatoriAdapterException):
    def __init__(self, response: Response):
        self.status_code: int = response.status_code
        self.code: Optional[int] = None
        self.message: Optional[str] = None
        self.data: Optional[dict] = None
        if response.content:
            body = json.loads(response.content)
            self._prepare_body(body)

    def __repr__(self) -> str:
        return (
            f"<ActionFailed: {self.status_code}, code={self.code}, "
            f"message={self.message}, data={self.data}>"
        )

    def __str__(self):
        return self.__repr__()

    def _prepare_body(self, body: dict):
        self.code = body.get("code")
        self.message = body.get("message")
        self.data = body.get("data")


class BadRequestException(ActionFailed):
    pass


class UnauthorizedException(ActionFailed):
    pass


class ForbiddenException(ActionFailed):
    pass


class NotFoundException(ActionFailed):
    pass


class MethodNotAllowedException(ActionFailed):
    pass


class ApiNotImplementedException(ActionFailed):
    pass


class NetworkError(BaseNetworkError, SatoriAdapterException):
    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg: Optional[str] = msg
        """错误原因"""

    def __repr__(self):
        return f"<NetWorkError message={self.msg}>"

    def __str__(self):
        return self.__repr__()


class ApiNotAvailable(BaseApiNotAvailable, SatoriAdapterException):
    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg: Optional[str] = msg
        """错误原因"""
