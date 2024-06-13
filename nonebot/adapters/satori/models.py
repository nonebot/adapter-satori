import mimetypes
from os import PathLike
from enum import IntEnum
from pathlib import Path
from datetime import datetime
from typing_extensions import TypeAlias
from typing import IO, Any, Union, Generic, Literal, TypeVar, Optional

from pydantic import Field, BaseModel
from nonebot.compat import PYDANTIC_V2, ConfigDict

from .utils import log
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
    ONLINE = 1
    CONNECT = 2
    DISCONNECT = 3
    RECONNECT = 4


class Login(BaseModel):
    user: Optional[User] = None
    self_id: Optional[str] = None
    platform: Optional[str] = None
    status: LoginStatus
    features: list[str] = Field(default_factory=list)
    proxy_urls: list[str] = Field(default_factory=list)

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class ArgvInteraction(BaseModel):
    name: str
    arguments: list
    options: Any


class ButtonInteraction(BaseModel):
    id: str


class Opcode(IntEnum):
    EVENT = 0
    PING = 1
    PONG = 2
    IDENTIFY = 3
    READY = 4


class Payload(BaseModel):
    op: Opcode = Field(...)
    body: Optional[dict[str, Any]] = Field(None)


class Identify(BaseModel):
    token: Optional[str] = None
    sequence: Optional[int] = None


class Ready(BaseModel):
    logins: list[Login]


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


class MessageObject(BaseModel):
    id: str
    content: str
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    member: Optional[Member] = None
    user: Optional[User] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    def ensure_content(cls, values):
        if "content" in values:
            return values
        log(
            "WARNING",
            "received message without content, " "this may be caused by a bug of Satori Server.",
        )
        return {**values, "content": "Unknown"}

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


class Event(BaseModel):
    id: int
    type: str
    platform: str
    self_id: str
    timestamp: datetime
    argv: Optional[ArgvInteraction] = None
    button: Optional[ButtonInteraction] = None
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    login: Optional[Login] = None
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

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class EventPayload(Payload):
    op: Literal[Opcode.EVENT] = Field(Opcode.EVENT)
    body: Event


PayloadType = Union[
    Union[EventPayload, PingPayload, PongPayload, IdentifyPayload, ReadyPayload],
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

    class PageDequeResult(PageResult[T]):
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
