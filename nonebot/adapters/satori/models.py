import mimetypes
from os import PathLike
from enum import IntEnum
from pathlib import Path
from datetime import datetime
from typing_extensions import TypeAlias
from typing import IO, Any, Union, Generic, Literal, TypeVar, Optional

from pydantic import Field, BaseModel
from nonebot.compat import PYDANTIC_V2, ConfigDict, model_dump

from .compat import field_validator, model_validator


class ChannelType(IntEnum):
    TEXT = 0
    DIRECT = 1
    CATEGORY = 2
    VOICE = 3


class Channel(BaseModel):
    id: str
    type: ChannelType
    name: Optional[str] = None
    parent_id: Optional[str] = None

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class Guild(BaseModel):
    id: str
    name: Optional[str] = None
    avatar: Optional[str] = None

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class User(BaseModel):
    id: str
    name: Optional[str] = None
    nick: Optional[str] = None
    avatar: Optional[str] = None
    is_bot: Optional[bool] = None

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class Member(BaseModel):
    user: Optional[User] = None
    nick: Optional[str] = None
    avatar: Optional[str] = None
    joined_at: Optional[datetime] = None

    @field_validator("joined_at", mode="before")
    def parse_joined_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as e:
            raise ValueError(f"invalid timestamp: {v}") from e
        return datetime.fromtimestamp(timestamp / 1000)

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class Role(BaseModel):
    id: str
    name: Optional[str] = None

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class LoginStatus(IntEnum):
    OFFLINE = 0
    """离线"""
    ONLINE = 1
    """在线"""
    CONNECT = 2
    """正在连接"""
    DISCONNECT = 3
    """正在断开连接"""
    RECONNECT = 4
    """正在重新连接"""


class Login(BaseModel):
    sn: int
    status: LoginStatus
    adapter: str
    platform: Optional[str] = None
    user: Optional[User] = None
    features: list[str] = Field(default_factory=list)

    @property
    def identity(self):
        if not self.user:
            raise ValueError(f"Login {self} has not complete yet")
        return f"{self.platform or 'satori'}:{self.user.id}"

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore
    else:

        class Config:
            extra = "allow"

    @model_validator(mode="before")
    def ensure_user(cls, values):
        if isinstance(values, dict):
            if "self_id" in values and "user" not in values:
                values["user"] = {"id": values["self_id"]}
            if "sn" not in values:
                values["sn"] = 0
            if "adapter" not in values:
                values["adapter"] = "satori"
            if "status" not in values:
                values["status"] = LoginStatus.ONLINE
        return values


class LoginOnline(Login):
    status: Literal[LoginStatus.ONLINE] = LoginStatus.ONLINE
    user: User  # type: ignore
    platform: str  # type: ignore


class ArgvInteraction(BaseModel):
    name: str
    arguments: list
    options: Any


class ButtonInteraction(BaseModel):
    id: str


class Opcode(IntEnum):
    EVENT = 0
    """事件 (接收)"""
    PING = 1
    """心跳 (发送)"""
    PONG = 2
    """心跳回复 (接收)"""
    IDENTIFY = 3
    """鉴权 (发送)"""
    READY = 4
    """鉴权成功 (接收)"""
    META = 5
    """元信息更新 (接收)"""


class Payload(BaseModel):
    op: Opcode = Field(...)
    body: Optional[dict[str, Any]] = Field(None)


class Identify(BaseModel):
    token: Optional[str] = None
    sn: Optional[int] = None


class Ready(BaseModel):
    logins: list[Login]
    proxy_urls: list[str] = Field(default_factory=list)


class Meta(BaseModel):
    logins: list[Login]
    proxy_urls: list[str] = Field(default_factory=list)


class MetaPartial(BaseModel):
    proxy_urls: list[str] = Field(default_factory=list)


class IdentifyPayload(Payload):
    op: Literal[Opcode.IDENTIFY] = Field(Opcode.IDENTIFY)
    body: Identify


class ReadyPayload(Payload):
    op: Literal[Opcode.READY] = Field(Opcode.READY)
    body: Ready


class PingPayload(Payload):
    op: Literal[Opcode.PING] = Field(Opcode.PING)


class PongPayload(Payload):
    op: Literal[Opcode.PONG] = Field(Opcode.PONG)


class MetaPayload(Payload):
    op: Literal[Opcode.META] = Field(Opcode.META)
    body: MetaPartial


class MessageObject(BaseModel):
    id: str
    content: str
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    member: Optional[Member] = None
    user: Optional[User] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("created_at", mode="before")
    def parse_created_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as e:
            raise ValueError(f"invalid timestamp: {v}") from e
        return datetime.fromtimestamp(timestamp / 1000)

    @field_validator("updated_at", mode="before")
    def parse_updated_at(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as e:
            raise ValueError(f"invalid timestamp: {v}") from e
        return datetime.fromtimestamp(timestamp / 1000)

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class MessageReceipt(MessageObject):
    content: Optional[str] = None  # type: ignore


class Event(BaseModel):
    type: str
    timestamp: datetime
    login: LoginOnline
    argv: Optional[ArgvInteraction] = None
    button: Optional[ButtonInteraction] = None
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    member: Optional[Member] = None
    message: Optional[MessageObject] = None
    operator: Optional[User] = None
    role: Optional[Role] = None
    user: Optional[User] = None

    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as e:
            raise ValueError(f"invalid timestamp: {v}") from e
        return datetime.fromtimestamp(timestamp / 1000)

    @model_validator(mode="before")
    def ensure_login(cls, values):
        if isinstance(values, dict):
            if "self_id" in values and "platform" in values:
                # log(
                #     "WARNING",
                #     "received event with `self_id` and `platform`, "
                #     "this may be caused by Satori Server used protocol under version 1.2.",
                # )
                if "login" not in values:
                    values["login"] = model_dump(
                        LoginOnline(
                            sn=values["self_id"],
                            status=LoginStatus.ONLINE,
                            adapter="satori",
                            platform=values["platform"],
                            user=User(id=values["self_id"]),
                        )
                    )
            if "id" in values and "sn" not in values:
                values["sn"] = values["id"]
        return values

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class EventPayload(Payload):
    op: Literal[Opcode.EVENT] = Field(Opcode.EVENT)
    body: dict


PayloadType = Union[
    Union[EventPayload, PingPayload, PongPayload, IdentifyPayload, ReadyPayload, MetaPayload],
    Payload,
]


T = TypeVar("T")


if PYDANTIC_V2:

    class PageResult(BaseModel, Generic[T]):
        data: list[T]
        next: Optional[str] = None

        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    class PageDequeResult(PageResult[T]):
        prev: Optional[str] = None

else:

    from pydantic.generics import GenericModel

    class PageResult(GenericModel, Generic[T]):
        data: list[T]
        next: Optional[str] = None

        class Config:
            extra = "allow"

    class PageDequeResult(PageResult[T], Generic[T]):
        prev: Optional[str] = None


Direction: TypeAlias = Literal["before", "after", "around"]
Order: TypeAlias = Literal["asc", "desc"]


class Upload:
    def __init__(
        self, file: Union[bytes, IO[bytes], PathLike], mimetype: str = "image/png", name: Optional[str] = None
    ):
        self.file = file
        self.mimetype = mimetype

        if isinstance(self.file, PathLike):
            self.mimetype = mimetypes.guess_type(str(self.file))[0] or self.mimetype
            self.name = Path(self.file).name
        else:
            self.name = name

    def dump(self):
        file = self.file

        if isinstance(file, PathLike):
            file = open(file, "rb")
        return self.name, file, self.mimetype
