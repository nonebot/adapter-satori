from enum import IntEnum
from datetime import datetime
from typing import Any, Dict, List, Union, Generic, Literal, TypeVar, Optional

from pydantic import Field, BaseModel, validator
from nonebot.compat import PYDANTIC_V2, ConfigDict

from .utils import log
from .compat import model_validator


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


class InnerMember(BaseModel):
    user: Optional[User] = None
    name: Optional[str] = None
    nick: Optional[str] = None
    avatar: Optional[str] = None
    joined_at: Optional[datetime] = None

    @validator("joined_at", pre=True)
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


class OuterMember(InnerMember):
    user: User
    joined_at: datetime


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

    if PYDANTIC_V2:
        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

    else:

        class Config:
            extra = "allow"


class OuterLogin(Login):
    user: User
    self_id: str
    platform: str


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
    body: Optional[Dict[str, Any]] = Field(None)


class Identify(BaseModel):
    token: Optional[str] = None
    sequence: Optional[int] = None


class Ready(BaseModel):
    logins: List[OuterLogin]


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


class InnerMessage(BaseModel):
    id: str
    content: str
    channel: Optional[Channel] = None
    guild: Optional[Guild] = None
    member: Optional[InnerMember] = None
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

    @validator("created_at", pre=True)
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

    @validator("updated_at", pre=True)
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


class OuterMessage(InnerMessage):
    channel: Channel
    guild: Guild
    user: User


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
    member: Optional[InnerMember] = None
    message: Optional[InnerMessage] = None
    operator: Optional[User] = None
    role: Optional[Role] = None
    user: Optional[User] = None

    @validator("timestamp", pre=True)
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

    class PageResult(BaseModel, Generic[T]):  # type: ignore
        data: List[T]
        next: Optional[str] = None

        model_config: ConfigDict = ConfigDict(extra="allow")  # type: ignore

else:

    from pydantic.generics import GenericModel

    class PageResult(GenericModel, Generic[T]):
        data: List[T]
        next: Optional[str] = None

        class Config:
            extra = "allow"
